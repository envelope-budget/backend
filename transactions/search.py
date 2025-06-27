import re
from datetime import datetime
from decimal import Decimal

from django.db.models import Exists, OuterRef, Q
from .models import SubTransaction


def parse_search_query(query_string, budget_id):
    """
    Parse a search query string and return a Django Q object for filtering transactions.
    Supports comma-separated queries and handles emojis and spaces in names.

    Features:
    - Comma-separated queries
    - Quoted phrases for exact matching
    - Individual word matching for non-quoted terms
    - Special filters with colon syntax (is:, in:, envelope:, etc.)

    Args:
        query_string (str): The search query string
        budget_id (str): The budget ID to scope the search

    Returns:
        Q: A Django Q object for filtering transactions
    """
    # Base filter for the budget
    base_filter = Q(budget_id=budget_id, deleted=False)

    # If query is empty, return all transactions for the budget
    if not query_string.strip():
        return base_filter

    # Split the query into comma-separated terms
    comma_separated_terms = _split_by_commas(query_string)

    # Initialize filters
    filters = Q()
    text_search_terms = []

    for term_group in comma_separated_terms:
        if not term_group:
            continue

        # Process each term group
        term_filters = _process_term_group(term_group, text_search_terms)
        filters &= term_filters

    # Add text search if there are any terms
    if text_search_terms:
        text_filter = _build_text_search_filter(text_search_terms)
        filters &= text_filter

    return base_filter & filters


def _split_by_commas(query_string):
    """
    Split the query by commas, preserving quoted sections.
    This ensures that commas inside quotes don't split the query.
    """
    result = []
    current = ""
    in_quotes = False

    for char in query_string:
        if char == '"':
            in_quotes = not in_quotes
            current += char
        elif char == "," and not in_quotes:
            result.append(current.strip())
            current = ""
        else:
            current += char

    if current:
        result.append(current.strip())

    return result


def _process_term_group(term_group, text_search_terms):
    """Process a group of terms (a single comma-separated section)"""
    # Check if this term group contains a filter operator
    filter_match = re.match(r"(\w+):(.*)", term_group)

    if filter_match:
        key = filter_match.group(1)
        value = filter_match.group(2).strip()

        # Handle different filter types
        if key == "is":
            return _parse_is_filter(value)
        elif key == "in":
            return _parse_in_filter(value)
        elif key == "envelope":
            return _parse_envelope_filter(value)
        elif key == "account":
            return _parse_account_filter(value)
        elif key == "after" or key == "since":
            return _parse_date_filter(value, ">=")
        elif key == "before":
            return _parse_date_filter(value, "<=")
        elif key == "on":
            return _parse_date_filter(value, "==")
        elif key == "amount":
            return _parse_amount_filter(value)
        elif key == "inflow":
            return _parse_inflow_filter(value)
        elif key == "outflow":
            return _parse_outflow_filter(value)
    else:
        # Check if this is a plain number (for amount search)
        number_match = re.match(r"^\d+\.?\d*$", term_group.strip())
        if number_match:
            return _parse_plain_number_filter(term_group.strip())
        
        # Process text search terms, handling quoted phrases
        _extract_search_terms(term_group, text_search_terms)

    return Q()


def _extract_search_terms(text, text_search_terms):
    """
    Extract search terms from text, handling quoted phrases.
    Quoted phrases are treated as a single term, while non-quoted text is split by spaces.
    """
    # Find all quoted phrases
    quoted_phrases = re.findall(r'"([^"]*)"', text)

    # Add quoted phrases as exact terms
    for phrase in quoted_phrases:
        if phrase:
            text_search_terms.append(phrase)

    # Remove quoted phrases from the text
    for phrase in quoted_phrases:
        text = text.replace(f'"{phrase}"', "")

    # Split remaining text by spaces and add non-empty terms
    for term in text.split():
        if term:
            text_search_terms.append(term)


def _parse_is_filter(value):
    """Parse 'is:X' filters"""
    if value == "cleared":
        return Q(cleared=True)
    elif value == "uncleared":
        return Q(cleared=False)
    elif value == "pending":
        return Q(pending=True)
    elif value == "archived":
        return Q(in_inbox=False)
    elif value == "unassigned":
        # A transaction is unassigned if:
        # 1. It has no envelope AND no subtransactions (regular unassigned transaction)
        # 2. OR it has subtransactions but some subtransactions don't have envelopes

        # Check if transaction has any subtransactions without envelopes
        has_unassigned_subtransactions = Exists(
            SubTransaction.objects.filter(
                transaction=OuterRef("pk"), envelope__isnull=True, deleted=False
            )
        )

        # Check if transaction has any subtransactions at all
        has_subtransactions = Exists(
            SubTransaction.objects.filter(transaction=OuterRef("pk"), deleted=False)
        )

        # Transaction is unassigned if:
        # (no envelope AND no subtransactions) OR (has unassigned subtransactions)
        return (
            Q(envelope__isnull=True) & ~has_subtransactions
        ) | has_unassigned_subtransactions
    elif value == "split":
        # A transaction is split if it has subtransactions
        return Exists(
            SubTransaction.objects.filter(transaction=OuterRef("pk"), deleted=False)
        )
    return Q()


def _parse_in_filter(value):
    """Parse 'in:X' filters"""
    if value == "inbox":
        return Q(in_inbox=True)
    elif value == "trash":
        return Q(deleted=True)
    return Q()


def _parse_envelope_filter(value):
    """Parse 'envelope:X' filters, supporting emojis and spaces"""
    return Q(envelope__name__icontains=value)


def _parse_account_filter(value):
    """Parse 'account:X' filters, supporting emojis and spaces"""
    return Q(account__name__icontains=value)


def _parse_date_filter(value, operator):
    """Parse date filters (after:, before:, on:)"""
    try:
        date_obj = datetime.strptime(value, "%Y-%m-%d").date()
        if operator == ">=":
            return Q(date__gte=date_obj)
        elif operator == "<=":
            return Q(date__lte=date_obj)
        elif operator == "==":
            return Q(date=date_obj)
    except ValueError:
        # Invalid date format, return empty filter
        return Q()
    return Q()


def _parse_amount_filter(value):
    """Parse 'amount:X' filters with support for comparison operators"""
    # Check for comparison operators
    match = re.match(r"([<>]=?|=)?(-?\d+\.?\d*)", value)
    if not match:
        return Q()

    operator, amount_str = match.groups()
    try:
        # Convert to milliunits (stored as integers in the database)
        amount = int(Decimal(amount_str) * 1000)

        if not operator or operator == "=":
            return Q(amount=amount)
        elif operator == ">":
            return Q(amount__gt=amount)
        elif operator == "<":
            return Q(amount__lt=amount)
        elif operator == ">=":
            return Q(amount__gte=amount)
        elif operator == "<=":
            return Q(amount__lte=amount)
    except (ValueError, TypeError):
        return Q()

    return Q()


def _parse_inflow_filter(value):
    """Parse 'inflow:X' filters (positive amounts)"""
    # Check for comparison operators
    match = re.match(r"([<>]=?|=)?(\d+\.?\d*)", value)
    if not match:
        return Q()

    operator, amount_str = match.groups()
    try:
        # Convert to milliunits (stored as integers in the database)
        amount = int(Decimal(amount_str) * 1000)

        if not operator or operator == "=":
            return Q(amount=amount)
        elif operator == ">":
            return Q(amount__gt=amount)
        elif operator == "<":
            return Q(amount__lt=amount)
        elif operator == ">=":
            return Q(amount__gte=amount)
        elif operator == "<=":
            return Q(amount__lte=amount)
    except (ValueError, TypeError):
        return Q()

    return Q() & Q(amount__gt=0)


def _parse_outflow_filter(value):
    """Parse 'outflow:X' filters (negative amounts)"""
    # Check for comparison operators
    match = re.match(r"([<>]=?|=)?(\d+\.?\d*)", value)
    if not match:
        return Q()

    operator, amount_str = match.groups()
    try:
        # Convert to milliunits (stored as integers in the database)
        amount = int(Decimal(amount_str) * 1000)
        # Negate the amount since outflows are stored as negative values
        amount = -amount

        if not operator or operator == "=":
            return Q(amount=amount)
        elif operator == ">":
            # For outflow, "greater than" means "more negative"
            return Q(amount__lt=amount)
        elif operator == "<":
            # For outflow, "less than" means "less negative"
            return Q(amount__gt=amount)
        elif operator == ">=":
            return Q(amount__lte=amount)
        elif operator == "<=":
            return Q(amount__gte=amount)
    except (ValueError, TypeError):
        return Q()

    return Q() & Q(amount__lt=0)


def _parse_plain_number_filter(value):
    """Parse plain number searches to match both inflow and outflow amounts"""
    try:
        # Convert to milliunits (stored as integers in the database)
        amount = int(Decimal(value) * 1000)
        
        # Match both positive (inflow) and negative (outflow) amounts
        return Q(amount=amount) | Q(amount=-amount)
    except (ValueError, TypeError):
        return Q()


def _build_text_search_filter(terms):
    """Build a filter for text search across multiple fields"""
    text_filter = Q()
    for term in terms:
        if not term:
            continue
        term_filter = (
            Q(payee__name__icontains=term)
            | Q(envelope__name__icontains=term)
            | Q(memo__icontains=term)
        )
        text_filter &= term_filter
    return text_filter
