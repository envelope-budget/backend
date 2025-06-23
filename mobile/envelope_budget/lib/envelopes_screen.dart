import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class EnvelopesScreen extends StatefulWidget {
  const EnvelopesScreen({super.key});

  @override
  State<EnvelopesScreen> createState() => _EnvelopesScreenState();
}

class _EnvelopesScreenState extends State<EnvelopesScreen> {
  List<dynamic> categories = [];
  bool _isLoading = false;
  String? _errorMessage;

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
    _loadEnvelopes();
  }

  Future<void> _loadEnvelopes() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // For now, just use mock data
      await Future.delayed(const Duration(milliseconds: 500)); // Simulate network delay

      setState(() {
        categories = _mockCategories;
        _isLoading = false;
      });

      /* TODO: Implement real API call
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('auth_token');
      final baseUrl = prefs.getString('base_url') ?? 'https://envelopebudget.com';

      if (token == null) {
        _showErrorMessage('No authentication token found');
        return;
      }

      const budgetId = 'your-budget-id-here';

      final response = await http.get(
        Uri.parse('$baseUrl/api/envelopes/$budgetId'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          categories = responseData;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = 'Failed to load envelopes: ${response.statusCode}';
          _isLoading = false;
        });
      }
      */
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

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadEnvelopes,
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
                      const SizedBox(height: 16),
                      Text(_errorMessage!, style: const TextStyle(fontSize: 16), textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadEnvelopes,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              : categories.isEmpty
                  ? const Center(child: Text('No envelopes found', style: TextStyle(fontSize: 16)))
                  : ListView.builder(
                      itemCount: categories.length,
                      itemBuilder: (context, index) {
                        final category = categories[index];
                        final envelopes = category['envelopes'] as List<dynamic>;

                        return Card(
                          margin: const EdgeInsets.all(8.0),
                          child: ExpansionTile(
                            title: Text(category['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                            subtitle: Text(
                              'Balance: ${_formatCurrency(category['balance'])}',
                              style: TextStyle(
                                color: category['balance'] >= 0 ? Colors.green : Colors.red,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            children: envelopes.map<Widget>((envelope) {
                              return ListTile(
                                leading: const Icon(Icons.mail_outline),
                                title: Text(envelope['name']),
                                trailing: Text(
                                  _formatCurrency(envelope['balance']),
                                  style: TextStyle(
                                    color: envelope['balance'] >= 0 ? Colors.green : Colors.red,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                onTap: () {
                                  // TODO: Navigate to envelope details
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text('${envelope['name']} details - Coming soon!')),
                                  );
                                },
                              );
                            }).toList(),
                          ),
                        );
                      },
                    ),
    );
  }
}
