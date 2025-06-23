import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'envelopes_screen.dart';
import 'transactions_screen.dart';
import 'add_transaction_screen.dart';
import 'main.dart';

class BudgetTabsScreen extends StatefulWidget {
  const BudgetTabsScreen({super.key});

  @override
  State<BudgetTabsScreen> createState() => _BudgetTabsScreenState();
}

class _BudgetTabsScreenState extends State<BudgetTabsScreen> {
  int _currentIndex = 0;
  String _selectedBudget = 'Personal Budget';

  // Mock budget data
  final List<String> _budgets = [
    'Personal Budget',
    'Family Budget',
    'Business Budget',
    'Vacation Fund',
  ];

  final List<Widget> _screens = [
    const EnvelopesScreen(),
    const TransactionsScreen(),
  ];

  void _showBudgetSelector() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return Container(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Select Budget',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              ...(_budgets.map((budget) => ListTile(
                leading: Icon(
                  _selectedBudget == budget ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                  color: Colors.green,
                ),
                title: Text(budget),
                onTap: () {
                  setState(() {
                    _selectedBudget = budget;
                  });
                  Navigator.pop(context);
                },
              ))),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: TextButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    // TODO: Implement create new budget
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Create new budget - Coming soon!')),
                    );
                  },
                  icon: const Icon(Icons.add),
                  label: const Text('Create New Budget'),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  void _showAddTransaction() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const AddTransactionScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        title: GestureDetector(
          onTap: _showBudgetSelector,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  _selectedBudget,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.keyboard_arrow_down),
            ],
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              // Only clear auth-related data, keep base_url
              await prefs.remove('auth_token');
              await prefs.remove('user_email');
              if (mounted) {
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (context) => const LoginScreen()),
                );
              }
            },
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        selectedItemColor: Colors.green,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.mail_outline),
            label: 'Envelopes',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.receipt_long),
            label: 'Transactions',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddTransaction,
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }
}
