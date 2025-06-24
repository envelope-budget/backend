import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class EnvelopesScreen extends StatefulWidget {
  final String budgetId; // Add budget ID parameter

  const EnvelopesScreen({super.key, required this.budgetId});

  @override
  State<EnvelopesScreen> createState() => _EnvelopesScreenState();
}

class _EnvelopesScreenState extends State<EnvelopesScreen> {
  List<dynamic> categories = [];
  bool _isLoading = false;
  String? _errorMessage;
  bool _quickViewMode = false;
  Set<String> _quickViewEnvelopes = {}; // Store envelope IDs for quick view

  // Mock data for now
  final List<Map<String, dynamic>> _mockCategories = [
    {
      'name': 'Essential',
      'balance': 125000, // $1,250.00
      'envelopes': [
        {'name': 'Rent/Mortgage', 'balance': 150000},
        {'name': 'Groceries', 'balance': 45000},
        {'name': 'Utilities', 'balance': 12000},
        {'name': 'Transportation', 'balance': -2500},
      ]
    },
    {
      'name': 'Lifestyle',
      'balance': 32500,
      'envelopes': [
        {'name': 'Dining Out', 'balance': 15000},
        {'name': 'Entertainment', 'balance': 8500},
        {'name': 'Shopping', 'balance': 9000},
      ]
    },
    {
      'name': 'Savings',
      'balance': 200000,
      'envelopes': [
        {'name': 'Emergency Fund', 'balance': 150000},
        {'name': 'Vacation', 'balance': 35000},
        {'name': 'New Car', 'balance': 15000},
      ]
    },
  ];

  @override
  void initState() {
    super.initState();
    _loadQuickViewPreferences(); // Load preferences first
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted) {
        _loadEnvelopes();
      }
    });
  }

  @override
  void didUpdateWidget(EnvelopesScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Reload when the budget ID changes
    if (oldWidget.budgetId != widget.budgetId) {
      _loadEnvelopes();
    }
  }

  Future<void> _loadEnvelopes() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      final baseUrl =
          prefs.getString('base_url') ?? 'https://envelopebudget.com';

      // Use the budget ID from widget parameter instead of SharedPreferences
      final budgetId = widget.budgetId;

      if (token == null) {
        setState(() {
          _errorMessage = 'No authentication token found';
          _isLoading = false;
        });
        return;
      }

      if (budgetId.isEmpty) {
        setState(() {
          _errorMessage = 'No budget ID provided';
          _isLoading = false;
        });
        return;
      }

      print('Making request to: $baseUrl/api/envelopes/$budgetId');
      print('Budget ID: $budgetId');
      print(
          'Token: ${token.substring(0, 20)}...'); // Only show first 20 chars for security

      final response = await http.get(
        Uri.parse('$baseUrl/api/envelopes/$budgetId'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      print('Response status: ${response.statusCode}');
      print('Response headers: ${response.headers}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body) as List<dynamic>;

        // Filter out hidden and deleted categories, and their hidden/deleted envelopes
        final filteredCategories = responseData.where((category) {
          return !(category['hidden'] == true || category['deleted'] == true);
        }).map((category) {
          // Filter envelopes within each category
          final envelopes =
              (category['envelopes'] as List<dynamic>).where((envelope) {
            return !(envelope['hidden'] == true || envelope['deleted'] == true);
          }).toList();

          // Sort envelopes by sort_order
          envelopes.sort(
              (a, b) => (a['sort_order'] ?? 0).compareTo(b['sort_order'] ?? 0));

          return {
            ...category,
            'envelopes': envelopes,
          };
        }).toList();

        // Sort categories by sort_order
        filteredCategories.sort(
            (a, b) => (a['sort_order'] ?? 0).compareTo(b['sort_order'] ?? 0));

        setState(() {
          categories = filteredCategories;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load envelopes: ${response.statusCode}';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Network error: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

  void _showErrorMessage(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  String _formatCurrency(int cents) {
    return '\$${(cents / 100).toStringAsFixed(2)}';
  }

  // Load quick view preferences from device storage
  Future<void> _loadQuickViewPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    final quickViewMode =
        prefs.getBool('quick_view_mode_${widget.budgetId}') ?? false;
    final quickViewEnvelopes =
        prefs.getStringList('quick_view_envelopes_${widget.budgetId}') ?? [];

    setState(() {
      _quickViewMode = quickViewMode;
      _quickViewEnvelopes = quickViewEnvelopes.toSet();
    });
  }

  // Save quick view preferences to device storage
  Future<void> _saveQuickViewPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('quick_view_mode_${widget.budgetId}', _quickViewMode);
    await prefs.setStringList('quick_view_envelopes_${widget.budgetId}',
        _quickViewEnvelopes.toList());
  }

  // Toggle quick view mode
  void _toggleQuickViewMode() {
    setState(() {
      _quickViewMode = !_quickViewMode;
    });
    _saveQuickViewPreferences();
  }

  // Toggle envelope in quick view
  void _toggleEnvelopeInQuickView(String envelopeId) {
    setState(() {
      if (_quickViewEnvelopes.contains(envelopeId)) {
        _quickViewEnvelopes.remove(envelopeId);
      } else {
        _quickViewEnvelopes.add(envelopeId);
      }
    });
    _saveQuickViewPreferences();
  }

  // Get filtered categories based on quick view preferences
  List<dynamic> _getFilteredCategories() {
    if (!_quickViewMode || _quickViewEnvelopes.isEmpty) {
      return _quickViewMode ? [] : categories;
    }

    return categories.where((category) {
      final envelopes =
          (category['envelopes'] as List<dynamic>).where((envelope) {
        return _quickViewEnvelopes.contains(envelope['id']?.toString() ?? '');
      }).toList();

      return envelopes.isNotEmpty;
    }).map((category) {
      return {
        ...category,
        'envelopes': (category['envelopes'] as List<dynamic>).where((envelope) {
          return _quickViewEnvelopes.contains(envelope['id']?.toString() ?? '');
        }).toList(),
      };
    }).toList();
  }

  // Show dialog to manage quick view envelopes
  void _showQuickViewSettings() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Quick View Settings'),
              content: SizedBox(
                width: double.maxFinite,
                height: 400,
                child: ListView.builder(
                  itemCount: categories.length,
                  itemBuilder: (context, categoryIndex) {
                    final category = categories[categoryIndex];
                    final envelopes = category['envelopes'] as List<dynamic>;

                    return ExpansionTile(
                      title: Text(category['name']),
                      children: envelopes.map<Widget>((envelope) {
                        final envelopeId = envelope['id']?.toString() ?? '';
                        final isSelected =
                            _quickViewEnvelopes.contains(envelopeId);

                        return CheckboxListTile(
                          title: Text(envelope['name']),
                          subtitle: Text(_formatCurrency(envelope['balance'])),
                          value: isSelected,
                          onChanged: (bool? value) {
                            setDialogState(() {
                              if (value == true) {
                                _quickViewEnvelopes.add(envelopeId);
                              } else {
                                _quickViewEnvelopes.remove(envelopeId);
                              }
                            });
                            setState(() {}); // Update main screen
                            _saveQuickViewPreferences();
                          },
                        );
                      }).toList(),
                    );
                  },
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () {
                    setDialogState(() {
                      _quickViewEnvelopes.clear();
                    });
                    setState(() {});
                    _saveQuickViewPreferences();
                  },
                  child: const Text('Clear All'),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Done'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  // Get filtered envelopes for quick view (flat list)
  List<Map<String, dynamic>> _getQuickViewEnvelopes() {
    List<Map<String, dynamic>> quickViewEnvelopes = [];

    for (final category in categories) {
      final envelopes = category['envelopes'] as List<dynamic>;
      for (final envelope in envelopes) {
        final envelopeId = envelope['id']?.toString() ?? '';
        if (_quickViewEnvelopes.contains(envelopeId)) {
          quickViewEnvelopes.add({
            ...envelope,
            'categoryName':
                category['name'], // Keep category name for reference
          });
        }
      }
    }

    return quickViewEnvelopes;
  }

  @override
  Widget build(BuildContext context) {
    final displayCategories = _getFilteredCategories();
    final quickViewEnvelopes = _getQuickViewEnvelopes();

    return Scaffold(
      appBar: AppBar(
        title: Text(_quickViewMode ? 'Quick View' : 'All Envelopes'),
        actions: [
          if (_quickViewMode)
            IconButton(
              icon: const Icon(Icons.settings),
              onPressed: _showQuickViewSettings,
              tooltip: 'Quick View Settings',
            ),
          IconButton(
            icon:
                Icon(_quickViewMode ? Icons.visibility : Icons.visibility_off),
            onPressed: _toggleQuickViewMode,
            tooltip: _quickViewMode ? 'Show All' : 'Quick View',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadEnvelopes,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _errorMessage != null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline,
                            size: 64, color: Colors.red[300]),
                        const SizedBox(height: 16),
                        Text(_errorMessage!,
                            style: const TextStyle(fontSize: 16),
                            textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _loadEnvelopes,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  )
                : _quickViewMode
                    ? _buildQuickView(quickViewEnvelopes)
                    : _buildFullView(displayCategories),
      ),
    );
  }

  // Build quick view with flat envelope list
  Widget _buildQuickView(List<Map<String, dynamic>> envelopes) {
    if (envelopes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'No envelopes selected for quick view',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _showQuickViewSettings,
              child: const Text('Select Envelopes'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: envelopes.length,
      itemBuilder: (context, index) {
        final envelope = envelopes[index];
        final balance = envelope['balance'] as int;

        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            leading: const Icon(Icons.mail_outline, size: 28),
            title: Text(
              envelope['name'],
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w500,
              ),
            ),
            subtitle: Text(
              envelope['categoryName'],
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
            trailing: Text(
              _formatCurrency(balance),
              style: TextStyle(
                color: balance >= 0 ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 20, // Bigger balance text
              ),
            ),
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('${envelope['name']} details - Coming soon!'),
                ),
              );
            },
          ),
        );
      },
    );
  }

  // Build full view with categories (existing logic)
  Widget _buildFullView(List<dynamic> displayCategories) {
    if (displayCategories.isEmpty) {
      return const Center(
        child: Text('No envelopes found', style: TextStyle(fontSize: 16)),
      );
    }

    return ListView.builder(
      itemCount: displayCategories.length,
      itemBuilder: (context, index) {
        final category = displayCategories[index];
        final envelopes = category['envelopes'] as List<dynamic>;

        return Card(
          margin: const EdgeInsets.all(8.0),
          child: ExpansionTile(
            title: Text(category['name'],
                style:
                    const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            subtitle: Text(
              'Balance: ${_formatCurrency(category['balance'])}',
              style: TextStyle(
                color: category['balance'] >= 0 ? Colors.green : Colors.red,
                fontWeight: FontWeight.w500,
              ),
            ),
            children: envelopes.map<Widget>((envelope) {
              final envelopeId = envelope['id']?.toString() ?? '';
              final isInQuickView = _quickViewEnvelopes.contains(envelopeId);

              return ListTile(
                leading: const Icon(Icons.mail_outline),
                title: Text(envelope['name']),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: Icon(
                        isInQuickView ? Icons.star : Icons.star_border,
                        color: isInQuickView ? Colors.amber : null,
                      ),
                      onPressed: () => _toggleEnvelopeInQuickView(envelopeId),
                      tooltip: isInQuickView
                          ? 'Remove from Quick View'
                          : 'Add to Quick View',
                    ),
                    Text(
                      _formatCurrency(envelope['balance']),
                      style: TextStyle(
                        color: envelope['balance'] >= 0
                            ? Colors.green
                            : Colors.red,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                        content:
                            Text('${envelope['name']} details - Coming soon!')),
                  );
                },
              );
            }).toList(),
          ),
        );
      },
    );
  }
}
