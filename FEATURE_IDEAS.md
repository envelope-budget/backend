# Smart Payee Names

When importing transactions, use AI to fix payee names.

Prompt could look something like this:

```json
{
  "model": "claude-3-7-sonnet-20250219",
  "max_tokens": 1000,
  "messages": [
    {
      "role": "user",
      "content": "Clean up the following payee names from financial transactions by:
      
1. Removing date prefixes (e.g., 'Visa - 07/10')
2. Removing store/location numbers when not needed for identification
3. Removing transaction codes and URL fragments
4. Fixing brand names to proper spelling and capitalization
5. Removing service indicators like 'Sp' (Shopping Purchase)
6. Keeping location information only when useful
7. Return a simple mapping of original names to cleaned names as JSON

Here are the payees to clean:

Visa - 05/03 Life Starfish Perks
Visa - 07/06 Nintendo Ca12331038
Visa - 07/07 Sp Moogoo Usa Moogo
[Insert all your payees here]"
    }
  ]
}
```

Perhaps cache payee names that have been converted before so you don't have to have AI change them again.

Skip ones that may have regex patterns in place to change them.

Consider using a local LLM to do this.
