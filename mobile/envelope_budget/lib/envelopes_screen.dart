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
    _loadQuickViewPreferences();
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted) {
        _loadEnvelopes();
      }
    });
  }

  @override
  void didUpdateWidget(EnvelopesScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
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
      print('Token: ${token.substring(0, 20)}...');

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

        final filteredCategories = responseData.where((category) {
          return !(category['hidden'] == true || category['deleted'] == true);
        }).map((category) {
          final envelopes =
              (category['envelopes'] as List<dynamic>).where((envelope) {
            return !(envelope['hidden'] == true || envelope['deleted'] == true);
          }).toList();

          envelopes.sort(
              (a, b) => (a['sort_order'] ?? 0).compareTo(b['sort_order'] ?? 0));

          return {
            ...category,
            'envelopes': envelopes,
          };
        }).toList();

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

  Future<void> _saveQuickViewPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('quick_view_mode_${widget.budgetId}', _quickViewMode);
    await prefs.setStringList('quick_view_envelopes_${widget.budgetId}',
        _quickViewEnvelopes.toList());
  }

  void _toggleQuickViewMode() {
    setState(() {
      _quickViewMode = !_quickViewMode;
    });
    _saveQuickViewPreferences();
  }

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

  void _showQuickViewSettings() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: Row(
                children: [
                  const Icon(Icons.star, color: Colors.amber),
                  const SizedBox(width: 8),
                  const Text('Quick View Settings'),
                ],
              ),
              content: SizedBox(
                width: double.maxFinite,
                height: 400,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Select envelopes to show in quick view (${_quickViewEnvelopes.length} selected)',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: ListView.builder(
                        itemCount: categories.length,
                        itemBuilder: (context, categoryIndex) {
                          final category = categories[categoryIndex];
                          final envelopes =
                              category['envelopes'] as List<dynamic>;

                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ExpansionTile(
                              title: Text(
                                category['name'],
                                style: const TextStyle(
                                    fontWeight: FontWeight.w500),
                              ),
                              subtitle: Text(
                                '${envelopes.where((e) => _quickViewEnvelopes.contains(e['id']?.toString() ?? '')).length}/${envelopes.length} selected',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                              children: envelopes.map<Widget>((envelope) {
                                final envelopeId =
                                    envelope['id']?.toString() ?? '';
                                final isSelected =
                                    _quickViewEnvelopes.contains(envelopeId);

                                return CheckboxListTile(
                                  dense: true,
                                  title: Text(
                                    envelope['name'],
                                    style: const TextStyle(fontSize: 14),
                                  ),
                                  subtitle: Text(
                                    _formatCurrency(envelope['balance']),
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: envelope['balance'] >= 0
                                          ? Colors.green
                                          : Colors.red,
                                    ),
                                  ),
                                  value: isSelected,
                                  activeColor: const Color(0xFF0071BC),
                                  onChanged: (bool? value) {
                                    setDialogState(() {
                                      if (value == true) {
                                        _quickViewEnvelopes.add(envelopeId);
                                      } else {
                                        _quickViewEnvelopes.remove(envelopeId);
                                      }
                                    });
                                    setState(() {});
                                    _saveQuickViewPreferences();
                                  },
                                );
                              }).toList(),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton.icon(
                  onPressed: () {
                    setDialogState(() {
                      _quickViewEnvelopes.clear();
                    });
                    setState(() {});
                    _saveQuickViewPreferences();
                  },
                  icon: const Icon(Icons.clear_all),
                  label: const Text('Clear All'),
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

  List<Map<String, dynamic>> _getQuickViewEnvelopes() {
    List<Map<String, dynamic>> quickViewEnvelopes = [];

    for (final category in categories) {
      final envelopes = category['envelopes'] as List<dynamic>;
      for (final envelope in envelopes) {
        final envelopeId = envelope['id']?.toString() ?? '';
        if (_quickViewEnvelopes.contains(envelopeId)) {
          quickViewEnvelopes.add({
            ...envelope,
            'categoryName': category['name'],
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
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).scaffoldBackgroundColor,
              border: Border(
                bottom: BorderSide(
                  color: Colors.grey.shade300,
                  width: 0.5,
                ),
              ),
            ),
            child: Row(
              children: [
                if (_quickViewMode) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0071BC).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: const Color(0xFF0071BC).withOpacity(0.3),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.filter_list,
                          size: 16,
                          color: const Color(0xFF0071BC),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Quick View (${_quickViewEnvelopes.length})',
                          style: TextStyle(
                            fontSize: 12,
                            color: const Color(0xFF0071BC),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                Expanded(
                  child: Text(
                    _quickViewMode
                        ? 'Showing selected envelopes'
                        : 'All envelopes',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ),
                if (_quickViewMode)
                  IconButton(
                    icon: const Icon(Icons.settings, size: 20),
                    onPressed: _showQuickViewSettings,
                    tooltip: 'Quick View Settings',
                    padding: EdgeInsets.zero,
                    constraints:
                        const BoxConstraints(minWidth: 32, minHeight: 32),
                  ),
                IconButton(
                  icon: Icon(
                    _quickViewMode ? Icons.visibility : Icons.visibility_off,
                    size: 20,
                    color: _quickViewMode ? const Color(0xFF0071BC) : null,
                  ),
                  onPressed: _toggleQuickViewMode,
                  tooltip: _quickViewMode ? 'Show All' : 'Quick View',
                  padding: EdgeInsets.zero,
                  constraints:
                      const BoxConstraints(minWidth: 32, minHeight: 32),
                ),
              ],
            ),
          ),
          Expanded(
            child: RefreshIndicator(
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
          ),
        ],
      ),
    );
  }

  Widget _buildQuickView(List<Map<String, dynamic>> envelopes) {
    if (envelopes.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.visibility_off,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            const Text(
              'No envelopes selected for quick view',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _showQuickViewSettings,
              icon: const Icon(Icons.settings),
              label: const Text('Select Envelopes'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      itemCount: envelopes.length,
      itemBuilder: (context, index) {
        final envelope = envelopes[index];
        final balance = envelope['balance'] as int;

        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
          elevation: 1,
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            leading: Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: balance >= 0 ? Colors.green : Colors.red,
                shape: BoxShape.circle,
              ),
            ),
            title: Text(
              envelope['name'],
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
            subtitle: Text(
              envelope['categoryName'],
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
            trailing: Text(
              _formatCurrency(balance),
              style: TextStyle(
                color: balance >= 0 ? Colors.green : Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 18,
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

  Widget _buildFullView(List<dynamic> displayCategories) {
    if (displayCategories.isEmpty) {
      return const Center(
        child: Text('No envelopes found', style: TextStyle(fontSize: 16)),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      itemCount: displayCategories.length,
      itemBuilder: (context, index) {
        final category = displayCategories[index];
        final envelopes = category['envelopes'] as List<dynamic>;

        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
          elevation: 1,
          child: Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              childrenPadding: EdgeInsets.zero,
              title: Text(
                category['name'],
                style:
                    const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              subtitle: Text(
                'Balance: ${_formatCurrency(category['balance'])}',
                style: TextStyle(
                  color: category['balance'] >= 0 ? Colors.green : Colors.red,
                  fontWeight: FontWeight.w500,
                  fontSize: 13,
                ),
              ),
              children: envelopes.map<Widget>((envelope) {
                final envelopeId = envelope['id']?.toString() ?? '';
                final isInQuickView = _quickViewEnvelopes.contains(envelopeId);

                return Container(
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(color: Colors.grey.shade200, width: 0.5),
                    ),
                  ),
                  child: ListTile(
                    contentPadding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                    leading: Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: envelope['balance'] >= 0
                            ? Colors.green
                            : Colors.red,
                        shape: BoxShape.circle,
                      ),
                    ),
                    title: Text(
                      envelope['name'],
                      style: const TextStyle(fontSize: 15),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        GestureDetector(
                          onTap: () => _toggleEnvelopeInQuickView(envelopeId),
                          child: Container(
                            padding: const EdgeInsets.all(4),
                            child: Icon(
                              isInQuickView ? Icons.star : Icons.star_border,
                              color: isInQuickView
                                  ? Colors.amber
                                  : Colors.grey[400],
                              size: 18,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          _formatCurrency(envelope['balance']),
                          style: TextStyle(
                            color: envelope['balance'] >= 0
                                ? Colors.green
                                : Colors.red,
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                            content: Text(
                                '${envelope['name']} details - Coming soon!')),
                      );
                    },
                  ),
                );
              }).toList(),
            ),
          ),
        );
      },
    );
  }
}
