import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'services/cache_service.dart';

class AddTransactionScreen extends StatefulWidget {
  const AddTransactionScreen({super.key});

  @override
  State<AddTransactionScreen> createState() => _AddTransactionScreenState();
}

class _AddTransactionScreenState extends State<AddTransactionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _payeeController = TextEditingController();
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
  bool _showPayeeSuggestions = false;
  
  final _envelopeSearchController = TextEditingController();

  List<Map<String, String>> _accounts = [];
  List<Map<String, dynamic>> _envelopes = [];
  List<Map<String, dynamic>> _categories = [];
  List<Map<String, String>> _payees = [];

  String? _budgetId;
  String? _authToken;
  String? _baseUrl;

  final _cacheService = CacheService();

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

  Future<void> _loadData({bool forceRefresh = false}) async {
    setState(() {
      _isLoadingData = true;
    });

    try {
      // First load user data
      await _loadUserData();
      
      // Invalidate cache if force refresh
      if (forceRefresh) {
        await _cacheService.invalidateAllCache(_budgetId!);
      }
      
      // Then load accounts, envelopes, and payees in parallel
      await Future.wait([
        _loadAccounts(),
        _loadEnvelopes(),
        _loadPayees(),
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

  Future<void> _refreshData() async {
    await _loadData(forceRefresh: true);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Data refreshed successfully!'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 1),
        ),
      );
    }
  }

  Future<void> _loadAccounts() async {
    try {
      // Check cache first
      final cachedAccounts = await _cacheService.getCachedAccounts(_budgetId!);
      if (cachedAccounts != null) {
        setState(() {
          _accounts = cachedAccounts;
        });
        return; // Use cached data
      }

      // Fetch from API if cache miss
      final response = await http.get(
        Uri.parse('$_baseUrl/api/accounts/$_budgetId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_authToken',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> accountsJson = json.decode(response.body);
        final accounts = accountsJson
            .map((account) => {
                  'id': account['id'] as String,
                  'name': account['name'] as String,
                })
            .toList();
        
        // Update cache
        await _cacheService.cacheAccounts(_budgetId!, accounts);
        
        setState(() {
          _accounts = accounts;
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
      // Check cache first
      final cachedData = await _cacheService.getCachedEnvelopes(_budgetId!);
      if (cachedData != null) {
        setState(() {
          _envelopes = cachedData['envelopes'] as List<Map<String, dynamic>>;
          _categories = cachedData['categories'] as List<Map<String, dynamic>>;
        });
        return; // Use cached data
      }

      // Fetch from API if cache miss
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
        
        // Update cache
        await _cacheService.cacheEnvelopes(_budgetId!, allEnvelopes, allCategories);
        
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

  Future<void> _loadPayees() async {
    try {
      // Check cache first
      final cachedPayees = await _cacheService.getCachedPayees(_budgetId!);
      if (cachedPayees != null) {
        setState(() {
          _payees = cachedPayees;
        });
        return; // Use cached data
      }

      // Fetch from API if cache miss
      final response = await http.get(
        Uri.parse('$_baseUrl/api/payees/$_budgetId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_authToken',
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> payeesJson = json.decode(response.body);
        final payees = payeesJson
            .map((payee) => {
                  'id': payee['id'] as String,
                  'name': payee['name'] as String,
                })
            .toList();
        // Sort payees alphabetically
        payees.sort((a, b) => a['name']!.compareTo(b['name']!));
        
        // Update cache
        await _cacheService.cachePayees(_budgetId!, payees);
        
        setState(() {
          _payees = payees;
        });
      } else {
        throw Exception('Failed to load payees: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error loading payees: $e');
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
          'payee': _payeeController.text.trim(),
          'envelope_id': _selectedEnvelope,
          'date': '${_selectedDate.year}-${_selectedDate.month.toString().padLeft(2, '0')}-${_selectedDate.day.toString().padLeft(2, '0')}',
          'amount': amountInCents.toInt(),
          'memo': _descriptionController.text.trim().isNotEmpty ? _descriptionController.text.trim() : null,
          'cleared': false,
          'reconciled': false,
        }),
      );

      if (response.statusCode == 200) {
        // Invalidate payee cache if a new payee was potentially created
        final payeeName = _payeeController.text.trim();
        final existingPayee = _payees.any((p) => p['name']!.toLowerCase() == payeeName.toLowerCase());
        if (!existingPayee) {
          await _cacheService.invalidatePayees(_budgetId!);
        }
        
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

  Widget _buildPayeeField() {
    if (_isLoadingData) {
      return TextFormField(
        enabled: false,
        decoration: InputDecoration(
          labelText: 'Payee',
          prefixIcon: const Icon(Icons.person, size: 20),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
          hintText: 'Loading payees...',
        ),
      );
    }

    return Column(
      children: [
        TextFormField(
          controller: _payeeController,
          decoration: InputDecoration(
            labelText: 'Payee',
            hintText: 'e.g., Walmart, Shell, Netflix, etc.',
            prefixIcon: const Icon(Icons.person, size: 20),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
            suffixIcon: _payeeController.text.isNotEmpty && _showPayeeSuggestions
                ? IconButton(
                    icon: const Icon(Icons.clear, size: 20),
                    onPressed: () {
                      setState(() {
                        _payeeController.clear();
                        _showPayeeSuggestions = false;
                      });
                    },
                  )
                : null,
          ),
          onChanged: (value) {
            setState(() {
              _showPayeeSuggestions = value.isNotEmpty;
            });
          },
          validator: (value) {
            if (value == null || value.trim().isEmpty) {
              return 'Please enter a payee';
            }
            return null;
          },
        ),
        if (_showPayeeSuggestions) ...[
          const SizedBox(height: 8),
          _buildPayeeSuggestions(),
        ],
      ],
    );
  }

  Widget _buildPayeeSuggestions() {
    final searchTerm = _payeeController.text.toLowerCase();
    final filteredPayees = _payees.where((payee) {
      final name = payee['name']!.toLowerCase();
      return name.contains(searchTerm);
    }).toList();

    if (filteredPayees.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey[300]!),
          borderRadius: BorderRadius.circular(8),
          color: Colors.grey[50],
        ),
        child: Text(
          'No existing payees found. "${_payeeController.text}" will be created as a new payee.',
          style: const TextStyle(color: Colors.grey, fontSize: 12),
        ),
      );
    }

    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(maxHeight: 120),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: filteredPayees.length,
        itemBuilder: (context, index) {
          final payee = filteredPayees[index];
          return ListTile(
            dense: true,
            title: Text(
              payee['name']!,
              style: const TextStyle(fontSize: 14),
            ),
            onTap: () {
              setState(() {
                _payeeController.text = payee['name']!;
                _showPayeeSuggestions = false;
              });
            },
          );
        },
      ),
    );
  }

  Widget _buildCompactEnvelopeSelector() {
    if (_isLoadingData) {
      return TextFormField(
        enabled: false,
        decoration: InputDecoration(
          labelText: 'Envelope (Optional)',
          prefixIcon: const Icon(Icons.mail_outline, size: 20),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
          hintText: 'Loading envelopes...',
        ),
      );
    }

    return Column(
      children: [
        // Search field if many envelopes, otherwise just dropdown
        if (_envelopes.length > 10) ...[
          TextFormField(
            controller: _envelopeSearchController,
            decoration: InputDecoration(
              labelText: 'Search Envelopes',
              prefixIcon: const Icon(Icons.search, size: 20),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
              suffixIcon: _envelopeSearchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear, size: 20),
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
          if (_isSearchingEnvelope) ...[
            const SizedBox(height: 8),
            _buildCompactSearchResults(),
          ] else ...[
            const SizedBox(height: 8),
            _buildCompactEnvelopeDropdown(),
          ],
        ] else
          _buildCompactEnvelopeDropdown(),
      ],
    );
  }

  Widget _buildCompactSearchResults() {
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
      constraints: const BoxConstraints(maxHeight: 150),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey[300]!),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: filteredEnvelopes.length + 1, // +1 for "No Envelope" option
        itemBuilder: (context, index) {
          if (index == 0) {
            return ListTile(
              dense: true,
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
            dense: true,
            title: Text(
              envelope['name'] as String,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 14),
            ),
            subtitle: Text(
              envelope['category_name'] as String,
              style: const TextStyle(fontSize: 11, color: Colors.grey),
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

  Widget _buildCompactEnvelopeDropdown() {
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
        decoration: InputDecoration(
          labelText: 'Envelope (Optional)',
          prefixIcon: const Icon(Icons.mail_outline, size: 20),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
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
          IconButton(
            onPressed: _isLoadingData ? null : _refreshData,
            icon: _isLoadingData
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.refresh),
            tooltip: 'Refresh data',
          ),
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            children: [
              // Amount Field - Compact but prominent
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Text(
                      'Amount',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        // Transaction Type Toggle - Compact
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.grey[300]!),
                          ),
                          child: ToggleButtons(
                            isSelected: [_isExpense, !_isExpense],
                            onPressed: (index) {
                              setState(() {
                                _isExpense = index == 0;
                              });
                            },
                            borderRadius: BorderRadius.circular(8),
                            selectedColor: Colors.white,
                            fillColor: _isExpense ? Colors.red[400] : Colors.green[400],
                            constraints: const BoxConstraints(minWidth: 40, minHeight: 32),
                            children: [
                              Icon(_isExpense ? Icons.remove : Icons.add, size: 16),
                              Icon(_isExpense ? Icons.add : Icons.trending_up, size: 16),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        // Amount Input
                        Expanded(
                          child: TextFormField(
                            controller: _amountController,
                            focusNode: _amountFocusNode,
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            inputFormatters: [
                              FilteringTextInputFormatter.allow(RegExp(r'^\d+\.?\d{0,2}')),
                            ],
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                              color: _isExpense ? Colors.red[600] : Colors.green[600],
                            ),
                            textAlign: TextAlign.right,
                            decoration: InputDecoration(
                              hintText: '0.00',
                              hintStyle: TextStyle(fontSize: 24, color: Colors.grey[400]),
                              prefixText: '\$ ',
                              prefixStyle: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: _isExpense ? Colors.red[600] : Colors.green[600],
                              ),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                              ),
                              contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
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
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // Main form fields in a card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Account Selector
                    SizedBox(
                      width: double.infinity,
                      child: DropdownButtonFormField<String>(
                      value: _selectedAccount,
                      decoration: InputDecoration(
                        labelText: 'Account',
                        prefixIcon: const Icon(Icons.account_balance, size: 20),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
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
                    const SizedBox(height: 12),

                    // Payee Field with Autocomplete
                    _buildPayeeField(),
                    const SizedBox(height: 12),

                    // Description Field (Optional)
                    TextFormField(
                      controller: _descriptionController,
                      decoration: InputDecoration(
                        labelText: 'Description (Optional)',
                        hintText: 'e.g., Weekly groceries, Gas fill-up, etc.',
                        prefixIcon: const Icon(Icons.description, size: 20),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Envelope Selector (Optional) - Compact
                    _buildCompactEnvelopeSelector(),
                    const SizedBox(height: 12),

                    // Date Selector
                    InkWell(
                      onTap: () => _selectDate(context),
                      child: InputDecorator(
                        decoration: InputDecoration(
                          labelText: 'Date',
                          prefixIcon: const Icon(Icons.calendar_today, size: 20),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
                        ),
                        child: Text(_formatDate(_selectedDate)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Save Button
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _saveTransaction,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0071BC),
                    foregroundColor: Colors.white,
                    elevation: 2,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Text(
                          'Save Transaction',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                        ),
                ),
              ),
              const SizedBox(height: 16), // Bottom padding for safe area
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _payeeController.dispose();
    _descriptionController.dispose();
    _amountController.dispose();
    _amountFocusNode.dispose();
    _envelopeSearchController.dispose();
    super.dispose();
  }
}
