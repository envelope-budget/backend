import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class TransactionsScreen extends StatefulWidget {
  final String budgetId;

  const TransactionsScreen({
    super.key,
    required this.budgetId,
  });

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  bool _isLoading = false;
  String _searchQuery = '';
  List<Map<String, dynamic>> _transactions = [];
  int _offset = 0;
  final int _limit = 20;
  bool _hasMoreData = true;

  @override
  void initState() {
    super.initState();
    if (widget.budgetId.isNotEmpty) {
      _loadTransactions();
    }
  }

  @override
  void didUpdateWidget(TransactionsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.budgetId != widget.budgetId && widget.budgetId.isNotEmpty) {
      _resetAndLoadTransactions();
    }
  }

  Future<void> _resetAndLoadTransactions() async {
    setState(() {
      _transactions = [];
      _offset = 0;
      _hasMoreData = true;
    });
    await _loadTransactions();
  }

  List<Map<String, dynamic>> get _filteredTransactions {
    var filtered = _transactions.where((transaction) {
      if (_searchQuery.isEmpty) return true;

      final memo = (transaction['memo'] ?? '').toString().toLowerCase();
      final payeeName =
          transaction['payee']?['name']?.toString().toLowerCase() ?? '';
      final envelopeName =
          transaction['envelope']?['name']?.toString().toLowerCase() ?? '';
      final accountName =
          transaction['account']?['name']?.toString().toLowerCase() ?? '';
      final query = _searchQuery.toLowerCase();

      return memo.contains(query) ||
          payeeName.contains(query) ||
          envelopeName.contains(query) ||
          accountName.contains(query);
    }).toList();

    return filtered;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.budgetId.isEmpty) {
      return const Center(
        child: Text('Please select a budget to view transactions'),
      );
    }

    return Scaffold(
      body: Column(
        children: [
          // Search Bar Section
          Container(
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor.withOpacity(0.1),
              border: Border(
                bottom: BorderSide(
                  color: Colors.grey.withOpacity(0.2),
                  width: 1,
                ),
              ),
            ),
            child: _buildSearchBar(),
          ),

          // Transaction List
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refreshTransactions,
              child: _buildTransactionList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return TextField(
      decoration: InputDecoration(
        hintText: 'Search transactions...',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: _searchQuery.isNotEmpty
            ? IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  setState(() {
                    _searchQuery = '';
                  });
                },
              )
            : null,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        filled: true,
        fillColor: Colors.grey[100],
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      onChanged: (value) {
        setState(() {
          _searchQuery = value;
        });
      },
    );
  }

  Widget _buildTransactionList() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    final transactions = _filteredTransactions;

    if (transactions.isEmpty) {
      return _buildEmptyState();
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: transactions.length,
      separatorBuilder: (context, index) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final transaction = transactions[index];
        return _buildTransactionCard(transaction);
      },
    );
  }

  Widget _buildTransactionCard(Map<String, dynamic> transaction) {
    final amount = transaction['amount'] as int;
    final isIncome = amount >= 0;
    final payeeName = transaction['payee']?['name'] ?? 'Unknown Payee';
    final envelopeName = transaction['envelope']?['name'] ?? 'Unassigned';
    final accountName = transaction['account']?['name'] ?? 'Unknown Account';
    final memo = transaction['memo'] ?? '';
    final isPending = transaction['pending'] ?? false;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showTransactionDetails(transaction),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: _getTransactionColor(amount).withOpacity(0.1),
                child: Icon(
                  _getTransactionIcon(envelopeName, isPending),
                  color: _getTransactionColor(amount),
                  size: 20,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      payeeName,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      envelopeName,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (memo.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        memo,
                        style: TextStyle(
                          color: Colors.grey[500],
                          fontSize: 12,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    const SizedBox(height: 2),
                    Text(
                      _formatDate(transaction['date']),
                      style: TextStyle(
                        color: Colors.grey[500],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${isIncome ? '+' : ''}${_formatCurrency(amount)}',
                    style: TextStyle(
                      color: _getTransactionColor(amount),
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (isPending) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.orange.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'PENDING',
                            style: TextStyle(
                              color: Colors.orange[700],
                              fontSize: 9,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                      ],
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.blue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          accountName.replaceAll(RegExp(r'[^\w\s]'), '').trim(),
                          style: TextStyle(
                            color: Colors.blue[700],
                            fontSize: 9,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.receipt_long_outlined,
              size: 80,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 24),
            Text(
              _searchQuery.isNotEmpty
                  ? 'No matching transactions'
                  : 'No transactions yet',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w600,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _searchQuery.isNotEmpty
                  ? 'Try adjusting your search terms'
                  : 'Start by adding your first transaction',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
              textAlign: TextAlign.center,
            ),
            if (_searchQuery.isEmpty) ...[
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () {
                  // TODO: Navigate to add transaction
                },
                icon: const Icon(Icons.add),
                label: const Text('Add Transaction'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showTransactionDetails(Map<String, dynamic> transaction) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (context, scrollController) {
          return _buildTransactionDetailsSheet(transaction, scrollController);
        },
      ),
    );
  }

  Widget _buildTransactionDetailsSheet(
    Map<String, dynamic> transaction,
    ScrollController scrollController,
  ) {
    final amount = transaction['amount'] as int;
    final payeeName = transaction['payee']?['name'] ?? 'Unknown Payee';
    final envelopeName = transaction['envelope']?['name'] ?? 'Unassigned';
    final accountName = transaction['account']?['name'] ?? 'Unknown Account';
    final memo = transaction['memo'] ?? '';
    final isPending = transaction['pending'] ?? false;
    final isCleared = transaction['cleared'] ?? false;
    final isReconciled = transaction['reconciled'] ?? false;

    return Container(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: _getTransactionColor(amount).withOpacity(0.1),
                child: Icon(
                  _getTransactionIcon(envelopeName, isPending),
                  color: _getTransactionColor(amount),
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      payeeName,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${amount >= 0 ? '+' : ''}${_formatCurrency(amount)}',
                      style: TextStyle(
                        fontSize: 18,
                        color: _getTransactionColor(amount),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          _buildDetailRow('Date', _formatDate(transaction['date'])),
          _buildDetailRow('Account', accountName),
          _buildDetailRow('Envelope', envelopeName),
          if (memo.isNotEmpty) _buildDetailRow('Memo', memo),
          _buildDetailRow(
              'Status', _getStatusText(isPending, isCleared, isReconciled)),
          _buildDetailRow('Transaction ID', transaction['id']),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    // TODO: Navigate to edit transaction
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                          content: Text(
                              'Edit transaction ${transaction['id']} - Coming soon!')),
                    );
                  },
                  icon: const Icon(Icons.edit),
                  label: const Text('Edit'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    _showDeleteConfirmation(transaction);
                  },
                  icon: const Icon(Icons.delete),
                  label: const Text('Delete'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getStatusText(bool isPending, bool isCleared, bool isReconciled) {
    if (isReconciled) return 'Reconciled';
    if (isCleared) return 'Cleared';
    if (isPending) return 'Pending';
    return 'Uncleared';
  }

  void _showDeleteConfirmation(Map<String, dynamic> transaction) {
    final payeeName = transaction['payee']?['name'] ?? 'Unknown Payee';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Transaction'),
        content: Text('Are you sure you want to delete "$payeeName"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              // TODO: Implement delete transaction
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Transaction deleted')),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'income':
        return Colors.green;
      case 'essential':
        return Colors.blue;
      case 'lifestyle':
        return Colors.orange;
      case 'savings':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  String _formatCurrency(int cents) {
    return '\$${(cents.abs() / 1000).toStringAsFixed(2)}';
  }

  String _formatDate(String dateStr) {
    final date = DateTime.parse(dateStr);
    final now = DateTime.now();
    final difference = now.difference(date).inDays;

    if (difference == 0) {
      return 'Today';
    } else if (difference == 1) {
      return 'Yesterday';
    } else if (difference < 7) {
      return '$difference days ago';
    } else {
      return '${date.month}/${date.day}/${date.year}';
    }
  }

  IconData _getTransactionIcon(String envelopeName, bool isPending) {
    if (isPending) return Icons.pending;

    final name = envelopeName.toLowerCase();
    if (name.contains('tithing') || name.contains('church')) {
      return Icons.church;
    }
    if (name.contains('groceries') || name.contains('food')) {
      return Icons.shopping_cart;
    }
    if (name.contains('medical') || name.contains('health')) {
      return Icons.medical_services;
    }
    if (name.contains('home') || name.contains('maintenance')) {
      return Icons.home_repair_service;
    }
    if (name.contains('clothing')) return Icons.checkroom;
    if (name.contains('crypto')) return Icons.currency_bitcoin;
    if (name.contains('gym') || name.contains('fitness')) {
      return Icons.fitness_center;
    }
    if (name.contains('reimbursement')) return Icons.receipt_long;

    return Icons.receipt;
  }

  Color _getTransactionColor(int amount) {
    return amount >= 0 ? Colors.green : Colors.red;
  }

  Future<void> _loadTransactions() async {
    if (_isLoading || widget.budgetId.isEmpty) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Get the base URL from shared preferences
      final prefs = await SharedPreferences.getInstance();
      final baseUrl =
          prefs.getString('base_url') ?? 'https://envelopebudget.com';
      final authToken = prefs.getString('auth_token') ?? '';

      // Debug: Check if budgetId is available
      print('Budget ID: ${widget.budgetId}');

      final url =
          '$baseUrl/api/transactions/${widget.budgetId}?offset=$_offset&limit=$_limit&in_inbox=true';
      print('API URL: $url'); // Debug: Print the full URL

      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
      );

      print(
          'Response status: ${response.statusCode}'); // Debug: Print response status

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<dynamic> items = data['items'] ?? [];

        setState(() {
          if (_offset == 0) {
            _transactions = items.cast<Map<String, dynamic>>();
          } else {
            _transactions.addAll(items.cast<Map<String, dynamic>>());
          }
          _hasMoreData = items.length == _limit;
          _offset += items.length;
        });
      } else {
        throw Exception('Failed to load transactions: ${response.statusCode}');
      }
    } catch (e) {
      print('Error loading transactions: $e'); // Debug: Print error
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error loading transactions: $e')),
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

  Future<void> _refreshTransactions() async {
    _offset = 0;
    _hasMoreData = true;
    await _loadTransactions();
  }
}
