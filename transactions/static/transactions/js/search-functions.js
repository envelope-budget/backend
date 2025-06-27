const SearchFunctions = {
  async loadSearchData() {
    try {
      // Use the shared envelope data manager if available
      if (window.envelopeDataManager) {
        const data = await window.envelopeDataManager.loadData();
        return {
          envelopes: data.envelopes,
          accounts: data.accounts,
        };
      }
      // Fallback to direct loading if manager not available
      return await this.loadSearchDataFallback();
    } catch (error) {
      console.error('Error loading search data:', error);
      // Try fallback method
      return await this.loadSearchDataFallback();
    }
  },

  async loadSearchDataFallback() {
    try {
      // Load envelopes data directly
      const envelopeResponse = await fetch('/envelopes/categorized_envelopes.json');
      const envelopeData = await envelopeResponse.json();
      const envelopes = envelopeData.categorized_envelopes.flatMap(category =>
        category.envelopes.map(envelope => ({
          id: envelope.id,
          name: envelope.name,
          categoryName: category.category.name,
        }))
      );

      // Load accounts data from the existing dropdown options
      let accounts = [];
      const accountSelect = document.getElementById('id_account');
      if (accountSelect) {
        accounts = Array.from(accountSelect.options)
          .filter(option => option.value && option.value !== '')
          .map(option => ({
            id: option.value,
            name: option.textContent,
          }));
      }

      return { envelopes, accounts };
    } catch (error) {
      console.error('Error in fallback search data loading:', error);
      return { envelopes: [], accounts: [] };
    }
  },

  generateSearchSuggestions(searchQuery, envelopes, accounts) {
    const suggestions = [];
    const currentTerm = this.getCurrentSearchTerm(searchQuery);

    if (!currentTerm) {
      return [];
    }

    const lowerTerm = currentTerm.toLowerCase();

    // Number-based suggestions (amount, inflow, outflow)
    const numberMatch = currentTerm.match(/^-?\d+\.?\d{0,2}$/);
    if (numberMatch) {
      const value = numberMatch[0];
      // Add outflow suggestions first (most common)
      suggestions.push(
        {
          display: `outflow:${value}`,
          description: 'Exact outflow amount',
          type: 'amount',
          value: `outflow:${value}`,
          priority: 1,
        },
        {
          display: `outflow:>${value}`,
          description: 'Outflow greater than',
          type: 'amount',
          value: `outflow:>${value}`,
          priority: 2,
        },
        {
          display: `outflow:>=${value}`,
          description: 'Outflow greater than or equal',
          type: 'amount',
          value: `outflow:>=${value}`,
          priority: 3,
        },
        {
          display: `outflow:<${value}`,
          description: 'Outflow less than',
          type: 'amount',
          value: `outflow:<${value}`,
          priority: 4,
        },
        {
          display: `outflow:<=${value}`,
          description: 'Outflow less than or equal',
          type: 'amount',
          value: `outflow:<=${value}`,
          priority: 5,
        },
        {
          display: `inflow:${value}`,
          description: 'Exact inflow amount',
          type: 'amount',
          value: `inflow:${value}`,
          priority: 6,
        },
        {
          display: `inflow:>${value}`,
          description: 'Inflow greater than',
          type: 'amount',
          value: `inflow:>${value}`,
          priority: 7,
        },
        {
          display: `inflow:>=${value}`,
          description: 'Inflow greater than or equal',
          type: 'amount',
          value: `inflow:>=${value}`,
          priority: 8,
        }
      );
    } else {
      // Status and location filters
      const statusFilters = [
        { key: 'is:cleared', description: 'Cleared transactions' },
        { key: 'is:uncleared', description: 'Uncleared transactions' },
        { key: 'is:pending', description: 'Pending transactions' },
        { key: 'is:unassigned', description: 'Unassigned transactions' },
        { key: 'is:split', description: 'Split transactions' },
        { key: 'in:inbox', description: 'Transactions in inbox' },
        { key: 'in:trash', description: 'Transactions in trash' },
      ];

      for (const filter of statusFilters) {
        if (filter.key.toLowerCase().includes(lowerTerm)) {
          suggestions.push({
            display: filter.key,
            description: filter.description,
            type: 'filter',
            value: filter.key,
            priority: 100,
          });
        }
      }

      // Envelope suggestions
      for (const envelope of envelopes) {
        if (envelope.name.toLowerCase().includes(lowerTerm)) {
          suggestions.push({
            display: `envelope:${envelope.name}`,
            description: `Filter by ${envelope.categoryName} envelope`,
            type: 'envelope',
            value: `envelope:${envelope.name}`,
            priority: 200,
          });
        }
      }

      // Account suggestions
      for (const account of accounts) {
        if (account.name.toLowerCase().includes(lowerTerm)) {
          suggestions.push({
            display: `account:${account.name}`,
            description: 'Filter by account',
            type: 'account',
            value: `account:${account.name}`,
            priority: 300,
          });
        }
      }

      // Sort non-number suggestions by relevance (exact matches first, then partial matches)
      suggestions.sort((a, b) => {
        const aExact = a.display.toLowerCase().startsWith(lowerTerm);
        const bExact = b.display.toLowerCase().startsWith(lowerTerm);

        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;

        // Then by priority, then alphabetically
        if (a.priority !== b.priority) return a.priority - b.priority;
        return a.display.localeCompare(b.display);
      });
    }

    return suggestions.slice(0, 8); // Limit to 8 suggestions for better UX
  },

  getCurrentSearchTerm(searchQuery) {
    const terms = searchQuery.split(',');
    const currentTerm = terms[terms.length - 1].trim();
    return currentTerm;
  },

  selectSuggestion(searchQuery, suggestion) {
    const terms = searchQuery.split(',');
    // Replace the last term with the selected suggestion
    terms[terms.length - 1] = ` ${suggestion.value}`;
    let newQuery = terms.join(',').trim();

    // Add a space and comma if this isn't the first term, to prepare for next input
    if (terms.length === 1) {
      newQuery += ', ';
    } else {
      newQuery += ', ';
    }

    return newQuery;
  },
};
