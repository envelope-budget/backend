import 'package:flutter/material.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key});

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  bool _isLoading = false;

  // Mock transaction data
  final List<Map<String, dynamic>> _mockTransactions = [
    {
      'id': '1',
      'date': '2024-01-15',
      'description': 'Grocery Store',
      'amount': -8500, // -$85.00
      'envelope': 'Groceries',
      'category': 'Essential',
    },
    {
      'id': '2',
      'date': '2024-01-14',
      'description': 'Salary Deposit',
      'amount': 350000, // $3,500.00
      'envelope': 'Income',
      'category': 'Income',
    },
    {
      'id': '3',
      'date': '2024-01-13',
      'description': 'Netflix Subscription',
      'amount': -1599, // -$15.99
      'envelope': 'Entertainment',
      'category': 'Lifestyle',
    },
    {
      'id': '4',
      'date': '2024-01-12',
      'description': 'Gas Station',
      'amount': -4200, // -$42.00
      'envelope': 'Transportation',
      'category': 'Essential',
    },
    {
      'id': '5',
      'date': '2024-01-11',
      'description': 'Restaurant',
      'amount': -2850, // -$28.50
      'envelope': 'Dining Out',
      'category': 'Lifestyle',
    },
    {
      'id': '6',
      'date': '2024-01-10',
      'description': 'Emergency Fund Transfer',
      'amount': 50000, // $500.00
      'envelope': 'Emergency Fund',
      'category': 'Savings',
    },
  ];

  String _formatCurrency(int cents) {
    return '\${(cents / 100).toStringAsFixed(2)}';
  }

  String _formatDate(String dateStr) {
    final date = DateTime.parse(dateStr);
    return '${date.month}/${date.day}/${date.year}';
  }

  IconData _getTransactionIcon(String category) {
    switch (category.toLowerCase()) {
      case 'income':
        return Icons.trending_up;
      case 'essential':
        return Icons.home;
      case 'lifestyle':
        return Icons.shopping_bag;
      case 'savings':
        return Icons.savings;
      default:
        return Icons.receipt;
    }
  }

  Color _getTransactionColor(int amount) {
    return amount >= 0 ? Colors.green : Colors.red;
  }

  Future<void> _loadTransactions() async {
    setState(() {
      _isLoading = true;
    });

    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 500));

    setState(() {
      _isLoading = false;
    });

    // TODO: Implement real API call
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadTransactions,
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _mockTransactions.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.receipt_long, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('No transactions found', style: TextStyle(fontSize: 16)),
                    ],
                  ),
                )
              : ListView.builder(
                  itemCount: _mockTransactions.length,
                  itemBuilder: (context, index) {
                    final transaction = _mockTransactions[index];
                    final amount = transaction['amount'] as int;
                    final isIncome = amount >= 0;

                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _getTransactionColor(amount).withOpacity(0.1),
                          child: Icon(
                            _getTransactionIcon(transaction['category']),
                            color: _getTransactionColor(amount),
                          ),
                        ),
                        title: Text(
                          transaction['description'],
                          style: const TextStyle(fontWeight: FontWeight.w500),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${transaction['envelope']} • ${_formatDate(transaction['date'])}',
                              style: TextStyle(color: Colors.grey[600]),
                            ),
                          ],
                        ),
                        trailing: Text(
                          '${isIncome ? '+' : ''}${_formatCurrency(amount)}',
                          style: TextStyle(
                            color: _getTransactionColor(amount),
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                        onTap: () {
                          // TODO: Navigate to transaction details
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Transaction ${transaction['id']} details - Coming soon!')),
                          );
                        },
                      ),
                    );
                  },
                ),
    );
  }
}
