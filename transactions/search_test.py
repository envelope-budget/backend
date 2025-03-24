from datetime import date, timedelta

from django.db.models import Q
from django.test import TestCase

from transactions.search import (
    parse_search_query,
    _parse_is_filter,
    _parse_in_filter,
    _parse_envelope_filter,
    _parse_account_filter,
    _parse_date_filter,
    _parse_amount_filter,
    _parse_inflow_filter,
    _parse_outflow_filter,
    _build_text_search_filter,
)


class SearchQueryParserTests(TestCase):
    def setUp(self):
        self.budget_id = "test-budget-id"
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)

    def test_empty_query(self):
        """Test that an empty query returns the base filter"""
        result = parse_search_query("", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False)
        self.assertEqual(str(result), str(expected))

    def test_whitespace_query(self):
        """Test that a whitespace query returns the base filter"""
        result = parse_search_query("   ", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False)
        self.assertEqual(str(result), str(expected))

    def test_text_search(self):
        """Test basic text search"""
        result = parse_search_query("grocery store", self.budget_id)
        expected = (
            Q(budget_id=self.budget_id, deleted=False)
            & Q(
                Q(payee__name__icontains="grocery")
                | Q(envelope__name__icontains="grocery")
                | Q(memo__icontains="grocery")
            )
            & Q(
                Q(payee__name__icontains="store")
                | Q(envelope__name__icontains="store")
                | Q(memo__icontains="store")
            )
        )
        self.assertEqual(str(result), str(expected))

    def test_is_cleared_filter(self):
        """Test is:cleared filter"""
        result = parse_search_query("is:cleared", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(cleared=True)
        self.assertEqual(str(result), str(expected))

    def test_is_uncleared_filter(self):
        """Test is:uncleared filter"""
        result = parse_search_query("is:uncleared", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(cleared=False)
        self.assertEqual(str(result), str(expected))

    def test_is_pending_filter(self):
        """Test is:pending filter"""
        result = parse_search_query("is:pending", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(pending=True)
        self.assertEqual(str(result), str(expected))

    def test_is_archived_filter(self):
        """Test is:archived filter"""
        result = parse_search_query("is:archived", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(in_inbox=False)
        self.assertEqual(str(result), str(expected))

    def test_in_inbox_filter(self):
        """Test in:inbox filter"""
        result = parse_search_query("in:inbox", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(in_inbox=True)
        self.assertEqual(str(result), str(expected))

    def test_in_trash_filter(self):
        """Test in:trash filter"""
        result = parse_search_query("in:trash", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(deleted=True)
        self.assertEqual(str(result), str(expected))

    def test_envelope_filter(self):
        """Test envelope filter with spaces and emoji"""
        result = parse_search_query("envelope:🍕 Food & Dining", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(
            envelope__name__icontains="🍕 Food & Dining"
        )
        self.assertEqual(str(result), str(expected))

    def test_account_filter(self):
        """Test account filter with spaces and emoji"""
        result = parse_search_query("account:💰 Checking Account", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(
            account__name__icontains="💰 Checking Account"
        )
        self.assertEqual(str(result), str(expected))

    def test_date_filters(self):
        """Test date filters (after, before, on)"""
        date_str = "2023-05-15"
        date_obj = date(2023, 5, 15)

        # Test after/since
        result = parse_search_query(f"after:{date_str}", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(date__gte=date_obj)
        self.assertEqual(str(result), str(expected))

        result = parse_search_query(f"since:{date_str}", self.budget_id)
        self.assertEqual(str(result), str(expected))

        # Test before
        result = parse_search_query(f"before:{date_str}", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(date__lte=date_obj)
        self.assertEqual(str(result), str(expected))

        # Test on
        result = parse_search_query(f"on:{date_str}", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(date=date_obj)
        self.assertEqual(str(result), str(expected))

    def test_amount_filters(self):
        """Test amount filters with various operators"""
        # Test exact amount
        result = parse_search_query("amount:100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(
            amount=100000
        )  # 100 * 1000
        self.assertEqual(str(result), str(expected))

        # Test negative amount
        result = parse_search_query("amount:-50.75", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(
            amount=-50750
        )  # -50.75 * 1000
        self.assertEqual(str(result), str(expected))

        # Test greater than
        result = parse_search_query("amount:>100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__gt=100000)
        self.assertEqual(str(result), str(expected))

        # Test less than
        result = parse_search_query("amount:<100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__lt=100000)
        self.assertEqual(str(result), str(expected))

        # Test greater than or equal
        result = parse_search_query("amount:>=100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__gte=100000)
        self.assertEqual(str(result), str(expected))

        # Test less than or equal
        result = parse_search_query("amount:<=100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__lte=100000)
        self.assertEqual(str(result), str(expected))

    def test_inflow_filters(self):
        """Test inflow filters (positive amounts)"""
        # Test exact inflow
        result = parse_search_query("inflow:100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount=100000)
        self.assertEqual(str(result), str(expected))

        # Test greater than
        result = parse_search_query("inflow:>100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__gt=100000)
        self.assertEqual(str(result), str(expected))

    def test_outflow_filters(self):
        """Test outflow filters (negative amounts)"""
        # Test exact outflow
        result = parse_search_query("outflow:100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount=-100000)
        self.assertEqual(str(result), str(expected))

        # Test greater than (more negative)
        result = parse_search_query("outflow:>100", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False) & Q(amount__lt=-100000)
        self.assertEqual(str(result), str(expected))

    def test_combined_filters(self):
        """Test combining multiple filters with commas"""
        result = parse_search_query(
            "is:cleared, envelope:🏠 Housing, amount:>100", self.budget_id
        )
        expected = (
            Q(budget_id=self.budget_id, deleted=False)
            & Q(cleared=True)
            & Q(envelope__name__icontains="🏠 Housing")
            & Q(amount__gt=100000)
        )
        self.assertEqual(str(result), str(expected))

    def test_combined_filters_with_text(self):
        """Test combining filters with free text search"""
        result = parse_search_query("grocery, is:cleared, amount:<-50", self.budget_id)
        expected = (
            Q(budget_id=self.budget_id, deleted=False)
            & Q(cleared=True)
            & Q(amount__lt=-50000)
            & Q(
                Q(payee__name__icontains="grocery")
                | Q(envelope__name__icontains="grocery")
                | Q(memo__icontains="grocery")
            )
        )
        self.assertEqual(str(result), str(expected))

    def test_invalid_date_format(self):
        """Test handling of invalid date format"""
        result = parse_search_query("after:not-a-date", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False)
        self.assertEqual(str(result), str(expected))

    def test_invalid_amount_format(self):
        """Test handling of invalid amount format"""
        result = parse_search_query("amount:not-a-number", self.budget_id)
        expected = Q(budget_id=self.budget_id, deleted=False)
        self.assertEqual(str(result), str(expected))

    def test_empty_comma_separated_terms(self):
        """Test handling of empty terms in comma-separated list"""
        result = parse_search_query("is:cleared, , amount:>100", self.budget_id)
        expected = (
            Q(budget_id=self.budget_id, deleted=False)
            & Q(cleared=True)
            & Q(amount__gt=100000)
        )
        self.assertEqual(str(result), str(expected))

    def test_quoted_phrase_search(self):
        """Test search with quoted phrases"""
        result = parse_search_query('"grocery store"', self.budget_id)

        # The quoted phrase should be searched as a single term
        phrase_filter = (
            Q(payee__name__icontains="grocery store")
            | Q(envelope__name__icontains="grocery store")
            | Q(memo__icontains="grocery store")
        )

        expected = Q(budget_id=self.budget_id, deleted=False) & phrase_filter

        self.assertEqual(str(result), str(expected))

    def test_mixed_quoted_and_unquoted_search(self):
        """Test search with both quoted and unquoted terms"""
        result = parse_search_query('walmart "grocery store"', self.budget_id)

        # The quoted phrase should be searched as a single term
        phrase_filter = (
            Q(payee__name__icontains="grocery store")
            | Q(envelope__name__icontains="grocery store")
            | Q(memo__icontains="grocery store")
        )

        # The unquoted term should be searched separately
        word_filter = (
            Q(payee__name__icontains="walmart")
            | Q(envelope__name__icontains="walmart")
            | Q(memo__icontains="walmart")
        )

        expected = (
            Q(budget_id=self.budget_id, deleted=False) & phrase_filter & word_filter
        )

        self.assertEqual(str(result), str(expected))

    def test_comma_in_quoted_phrase(self):
        """Test that commas inside quotes don't split the query"""
        result = parse_search_query('"food, dining"', self.budget_id)

        # The quoted phrase with comma should be treated as a single term
        phrase_filter = (
            Q(payee__name__icontains="food, dining")
            | Q(envelope__name__icontains="food, dining")
            | Q(memo__icontains="food, dining")
        )

        expected = Q(budget_id=self.budget_id, deleted=False) & phrase_filter

        self.assertEqual(str(result), str(expected))

    # def test_quoted_phrase_with_filter(self):
    #     """Test combining quoted phrases with filters"""
    #     result = parse_search_query('"grocery store", is:cleared', self.budget_id)

    #     # The quoted phrase should be searched as a single term
    #     phrase_filter = (
    #         Q(payee__name__icontains="grocery store")
    #         | Q(envelope__name__icontains="grocery store")
    #         | Q(memo__icontains="grocery store")
    #     )

    #     expected = (
    #         Q(budget_id=self.budget_id, deleted=False) & phrase_filter & Q(cleared=True)
    #     )

    #     self.assertEqual(str(result), str(expected))


class SearchHelperFunctionTests(TestCase):
    """Tests for individual helper functions in search.py"""

    def test_parse_is_filter(self):
        self.assertEqual(str(_parse_is_filter("cleared")), str(Q(cleared=True)))
        self.assertEqual(str(_parse_is_filter("uncleared")), str(Q(cleared=False)))
        self.assertEqual(str(_parse_is_filter("pending")), str(Q(pending=True)))
        self.assertEqual(str(_parse_is_filter("archived")), str(Q(in_inbox=False)))
        self.assertEqual(str(_parse_is_filter("invalid")), str(Q()))

    def test_parse_in_filter(self):
        self.assertEqual(str(_parse_in_filter("inbox")), str(Q(in_inbox=True)))
        self.assertEqual(str(_parse_in_filter("trash")), str(Q(deleted=True)))
        self.assertEqual(str(_parse_in_filter("invalid")), str(Q()))

    def test_parse_envelope_filter(self):
        self.assertEqual(
            str(_parse_envelope_filter("Groceries")),
            str(Q(envelope__name__icontains="Groceries")),
        )
        self.assertEqual(
            str(_parse_envelope_filter("🍕 Food & Dining")),
            str(Q(envelope__name__icontains="🍕 Food & Dining")),
        )

    def test_parse_account_filter(self):
        self.assertEqual(
            str(_parse_account_filter("Checking")),
            str(Q(account__name__icontains="Checking")),
        )
        self.assertEqual(
            str(_parse_account_filter("💰 Savings Account")),
            str(Q(account__name__icontains="💰 Savings Account")),
        )

    def test_parse_date_filter(self):
        date_obj = date(2023, 5, 15)
        self.assertEqual(
            str(_parse_date_filter("2023-05-15", ">=")), str(Q(date__gte=date_obj))
        )
        self.assertEqual(
            str(_parse_date_filter("2023-05-15", "<=")), str(Q(date__lte=date_obj))
        )
        self.assertEqual(
            str(_parse_date_filter("2023-05-15", "==")), str(Q(date=date_obj))
        )
        self.assertEqual(str(_parse_date_filter("invalid", ">=")), str(Q()))
