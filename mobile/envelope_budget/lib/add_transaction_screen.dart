import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class AddTransactionScreen extends StatefulWidget {
  const AddTransactionScreen({super.key});

  @override
  State<AddTransactionScreen> createState() => _AddTransactionScreenState();
}

class _AddTransactionScreenState extends State<AddTransactionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _descriptionController = TextEditingController();
  final _amountController = TextEditingController();
  final _amountFocusNode = FocusNode();

  String? _selectedAccount;
  String? _selectedEnvelope;
  DateTime _selectedDate = DateTime.now();
  bool _isExpense = true;
  bool _isLoading = false;
  bool _isLoadingData = true;
  bool _isSearchingEnvelope = false;
  
  final _envelopeSearchController = TextEditingController();

  List<Map<String, String>> _accounts = [];
  List<Map<String, dynamic>> _envelopes = [];
  List<Map<String, dynamic>> _categories = [];

  String? _budgetId;
  String? _authToken;
  String? _baseUrl;

  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  String _formatDate(DateTime date) {
    return '${date.month}/${date.day}/${date.year}';
  }

  Future<void> _loadUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _budgetId = prefs.getString('budget_id');
      _authToken = prefs.getString('auth_token');
      _baseUrl = prefs.getString('base_url') ?? 'https://envelopebudget.com';

      if (_budgetId == null || _authToken == null) {
        throw Exception('Missing authentication data. Please log in again.');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading user data: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
        Navigator.pop(context); // Return to previous screen
      }
      return;
    }
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoadingData = true;
    });

    try {
      // First load user data
      await _loadUserData();
      
      // Then load accounts and envelopes in parallel
      await Future.wait([
        _loadAccounts(),
        _loadEnvelopes(),
      ]);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error loading data: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingData = false;
        });
      }
    }
  }

  Future<void> _loadAccounts() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/api/accounts/$_budgetId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_authToken',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> accountsJson = json.decode(response.body);
        setState(() {
          _accounts = accountsJson
              .map((account) => {
                    'id': account['id'] as String,
                    'name': account['name'] as String,
                  })
              .toList();
        });
      } else {
        throw Exception('Failed to load accounts: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error loading accounts: $e');
    }
  }

  Future<void> _loadEnvelopes() async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/api/envelopes/$_budgetId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_authToken',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> categoriesJson = json.decode(response.body);
        final List<Map<String, dynamic>> allEnvelopes = [];
        final List<Map<String, dynamic>> allCategories = [];
        
        // Process categories and their envelopes
        for (final category in categoriesJson) {
          allCategories.add({
            'id': category['id'] as String,
            'name': category['name'] as String,
            'sort_order': category['sort_order'] as int,
          });
          
          final List<dynamic> envelopes = category['envelopes'] ?? [];
          // Sort envelopes by sort_order within each category
          envelopes.sort((a, b) => (a['sort_order'] as int).compareTo(b['sort_order'] as int));
          
          for (final envelope in envelopes) {
            allEnvelopes.add({
              'id': envelope['id'] as String,
              'name': envelope['name'] as String,
              'category_id': category['id'] as String,
              'category_name': category['name'] as String,
              'sort_order': envelope['sort_order'] as int,
              'category_sort_order': category['sort_order'] as int,
            });
          }
        }
        
        // Sort categories by sort_order
        allCategories.sort((a, b) => (a['sort_order'] as int).compareTo(b['sort_order'] as int));
        
        setState(() {
          _envelopes = allEnvelopes;
          _categories = allCategories;
        });
      } else {
        throw Exception('Failed to load envelopes: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error loading envelopes: $e');
    }
  }

  Future<void> _saveTransaction() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final amount = double.parse(_amountController.text);
      final amountInCents = (_isExpense ? -amount : amount) * 1000; // Convert to cents and make negative for expenses

      final response = await http.post(
        Uri.parse('$_baseUrl/api/transactions/$_budgetId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_authToken',
        },
        body: json.encode({
          'account_id': _selectedAccount,
          'payee': _descriptionController.text,
          'envelope_id': _selectedEnvelope,
          'date': '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
          'amount': amountInCents.toInt(),
          'memo': null,
          'cleared': false,
          'reconciled': false,
        }),
      );

      if (response.statusCode == 200) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Transaction saved successfully!'),
              backgroundColor: Colors.green,
            ),
          );
          Navigator.pop(context);
        }
      } else {
        throw Exception('Failed to save transaction: ${response.statusCode}');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error saving transaction: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Widget _buildEnvelopeSelector() {
    if (_isLoadingData) {
      return TextFormField(
        enabled: false,
        decoration: const InputDecoration(
          labelText: 'Envelope (Optional)',
          prefixIcon: Icon(Icons.mail_outline),
          border: OutlineInputBorder(),
          hintText: 'Loading envelopes...',
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Search field
        TextFormField(
          controller: _envelopeSearchController,
          decoration: InputDecoration(
            labelText: 'Search Envelopes',
            prefixIcon: const Icon(Icons.search),
            border: const OutlineInputBorder(),
            suffixIcon: _envelopeSearchController.text.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear),
                    onPressed: () {
                      setState(() {
                        _envelopeSearchController.clear();
                        _isSearchingEnvelope = false;
                      });
                    },
                  )
                : null,
          ),
          onChanged: (value) {
            setState(() {
              _isSearchingEnvelope = value.isNotEmpty;
            });
          },
        ),
        const SizedBox(height: 8),
        
        // Current selection display and dropdown
        _isSearchingEnvelope ? _buildSearchResults() : _buildEnvelopeDropdown(),
      ],
    );
  }

  Widget _buildSearchResults() {
    final searchTerm = _envelopeSearchController.text.toLowerCase();
    final filteredEnvelopes = _envelopes.where((envelope) {
      final name = (envelope['name'] as String).toLowerCase();
      final categoryName = (envelope['category_name'] as String).toLowerCase();
      return name.contains(searchTerm) || categoryName.contains(searchTerm);
    }).toList();

    if (filteredEnvelopes.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey),
          borderRadius: BorderRadius.circular(4),
        ),
        child: const Text(
          'No envelopes found',
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(maxHeight: 200),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(4),
      ),
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: filteredEnvelopes.length + 1, // +1 for "No Envelope" option
        itemBuilder: (context, index) {
          if (index == 0) {
            return ListTile(
              title: const Text('No Envelope'),
              onTap: () {
                setState(() {
                  _selectedEnvelope = null;
                  _envelopeSearchController.clear();
                  _isSearchingEnvelope = false;
                });
              },
              selected: _selectedEnvelope == null,
            );
          }
          
          final envelope = filteredEnvelopes[index - 1];
          return ListTile(
            title: Text(
              envelope['name'] as String,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(
              envelope['category_name'] as String,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            onTap: () {
              setState(() {
                _selectedEnvelope = envelope['id'] as String;
                _envelopeSearchController.clear();
                _isSearchingEnvelope = false;
              });
            },
            selected: _selectedEnvelope == envelope['id'],
          );
        },
      ),
    );
  }

  Widget _buildEnvelopeDropdown() {
    // Build organized dropdown items
    final List<DropdownMenuItem<String>> items = [
      const DropdownMenuItem(
        value: null,
        child: Text('No Envelope'),
      ),
    ];

    // Group envelopes by category and sort properly
    final Map<String, List<Map<String, dynamic>>> envelopesByCategory = {};
    for (final envelope in _envelopes) {
      final categoryId = envelope['category_id'] as String;
      if (!envelopesByCategory.containsKey(categoryId)) {
        envelopesByCategory[categoryId] = [];
      }
      envelopesByCategory[categoryId]!.add(envelope);
    }

    // Sort categories by sort_order and add envelopes
    for (final category in _categories) {
      final categoryId = category['id'] as String;
      final categoryName = category['name'] as String;
      final categoryEnvelopes = envelopesByCategory[categoryId] ?? [];

      if (categoryEnvelopes.isNotEmpty) {
        // Add category header (disabled item)
        items.add(DropdownMenuItem(
          value: 'header_$categoryId',
          enabled: false,
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Text(
              '── $categoryName ──',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey,
                fontSize: 12,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ));

        // Add envelopes in this category (already sorted)
        for (final envelope in categoryEnvelopes) {
          items.add(DropdownMenuItem(
            value: envelope['id'] as String,
            child: Padding(
              padding: const EdgeInsets.only(left: 16),
              child: Text(
                envelope['name'] as String,
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ),
          ));
        }
      }
    }

    return SizedBox(
      width: double.infinity,
      child: DropdownButtonFormField<String>(
        value: _selectedEnvelope,
        decoration: const InputDecoration(
          labelText: 'Envelope (Optional)',
          prefixIcon: Icon(Icons.mail_outline),
          border: OutlineInputBorder(),
        ),
        items: items,
        selectedItemBuilder: (BuildContext context) {
          return items.map<Widget>((item) {
            if (item.value == _selectedEnvelope && _selectedEnvelope != null) {
              final envelope = _envelopes.firstWhere(
                (env) => env['id'] == _selectedEnvelope,
                orElse: () => {'name': 'Unknown'},
              );
              return Text(
                envelope['name'] as String,
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              );
            }
            return Text(
              item.value == null ? 'No Envelope' : '',
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            );
          }).toList();
        },
        onChanged: (value) {
          // Prevent selection of header items
          if (value != null && value.startsWith('header_')) {
            return;
          }
          setState(() {
            _selectedEnvelope = value;
          });
        },
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    // Load accounts and envelopes data
    _loadData();
    // Auto-focus the amount field when the screen opens
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _amountFocusNode.requestFocus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Transaction'),
        backgroundColor: const Color(0xFF0071BC),
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: _isLoading ? null : _saveTransaction,
            child: _isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Text(
                    'Save',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Amount Field - Large and prominent at the top
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  children: [
                    Text(
                      'Enter Amount',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _amountController,
                      focusNode: _amountFocusNode,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      inputFormatters: [
                        FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
                      ],
                      style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                      decoration: InputDecoration(
                        hintText: '0.00',
                        hintStyle: TextStyle(fontSize: 32, color: Colors.grey[400]),
                        prefixIcon: Icon(
                          Icons.attach_money,
                          size: 32,
                          color: _isExpense ? Colors.red : const Color(0xFF0071BC),
                        ),
                        prefixText: _isExpense ? '-\$' : '+\$',
                        prefixStyle: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: _isExpense ? Colors.red : const Color(0xFF0071BC),
                        ),
                        border: const OutlineInputBorder(),
                        contentPadding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Please enter an amount';
                        }
                        final amount = double.tryParse(value);
                        if (amount == null || amount <= 0) {
                          return 'Please enter a valid amount';
                        }
                        return null;
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Transaction Type Toggle
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Transaction Type',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ToggleButtons(
                      isSelected: [_isExpense, !_isExpense],
                      onPressed: (index) {
                        setState(() {
                          _isExpense = index == 0;
                        });
                      },
                      borderRadius: BorderRadius.circular(8),
                      selectedColor: Colors.white,
                      fillColor: _isExpense ? Colors.red : Colors.green,
                      children: const [
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 24),
                          child: Text('Expense'),
                        ),
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 24),
                          child: Text('Income'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Account Selector
            SizedBox(
              width: double.infinity,
              child: DropdownButtonFormField<String>(
              value: _selectedAccount,
              decoration: InputDecoration(
                labelText: 'Account',
                prefixIcon: const Icon(Icons.account_balance),
                border: const OutlineInputBorder(),
                enabled: !_isLoadingData,
              ),
              items: _isLoadingData
                  ? [
                      const DropdownMenuItem(
                        value: null,
                        child: Text('Loading accounts...'),
                      )
                    ]
                  : _accounts.map((account) {
                      return DropdownMenuItem(
                        value: account['id'],
                        child: SizedBox(
                          width: double.infinity,
                          child: Text(
                            account['name']!,
                            overflow: TextOverflow.ellipsis,
                            maxLines: 1,
                          ),
                        ),
                      );
                    }).toList(),
              selectedItemBuilder: (BuildContext context) {
                return _accounts.map<Widget>((account) {
                  return Text(
                    account['name']!,
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  );
                }).toList();
              },
              onChanged: _isLoadingData
                  ? null
                  : (value) {
                      setState(() {
                        _selectedAccount = value;
                      });
                    },
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please select an account';
                }
                return null;
              },
              ),
            ),
            const SizedBox(height: 16),

            // Description Field
            TextFormField(
              controller: _descriptionController,
              decoration: const InputDecoration(
                labelText: 'Description',
                hintText: 'e.g., Grocery Store, Salary, etc.',
                prefixIcon: Icon(Icons.description),
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter a description';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),

            // Envelope Selector (Optional)
            _buildEnvelopeSelector(),
            const SizedBox(height: 16),

            // Date Selector
            InkWell(
              onTap: () => _selectDate(context),
              child: InputDecorator(
                decoration: const InputDecoration(
                  labelText: 'Date',
                  prefixIcon: Icon(Icons.calendar_today),
                  border: OutlineInputBorder(),
                ),
                child: Text(_formatDate(_selectedDate)),
              ),
            ),
            const SizedBox(height: 32),

            // Save Button (Alternative to AppBar action)
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _saveTransaction,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF0071BC),
                  foregroundColor: Colors.white,
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      )
                    : const Text(
                        'Save Transaction',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    _amountController.dispose();
    _amountFocusNode.dispose();
    _envelopeSearchController.dispose();
    super.dispose();
  }
}
