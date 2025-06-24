import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'envelopes_screen.dart';
import 'transactions_screen.dart';
import 'add_transaction_screen.dart';
import 'main.dart';
import 'services/api_service.dart';

class BudgetTabsScreen extends StatefulWidget {
  const BudgetTabsScreen({super.key});

  @override
  State<BudgetTabsScreen> createState() => _BudgetTabsScreenState();
}

class _BudgetTabsScreenState extends State<BudgetTabsScreen> {
  int _currentIndex = 0;
  String _selectedBudgetId = '';
  String _selectedBudgetName = 'Loading...';
  List<Budget> _budgets = [];
  bool _isLoadingBudgets = true;

  late List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    _screens = [
      EnvelopesScreen(key: ValueKey(_selectedBudgetId)),
      const TransactionsScreen(),
    ];
    _loadBudgets().then((_) => _loadSavedBudgetId());
  }

  void _updateScreens() {
    setState(() {
      _screens = [
        EnvelopesScreen(key: ValueKey(_selectedBudgetId)),
        const TransactionsScreen(),
      ];
    });
  }

  Future<void> _loadBudgets() async {
    try {
      setState(() {
        _isLoadingBudgets = true;
      });

      final budgets = await ApiService.getBudgets();

      setState(() {
        _budgets = budgets;
        _isLoadingBudgets = false;

        // Set the first budget as selected if available
        if (budgets.isNotEmpty && _selectedBudgetId.isEmpty) {
          _selectedBudgetId = budgets.first.id;
          _selectedBudgetName = budgets.first.name;
          _saveBudgetId(_selectedBudgetId);
          _updateScreens();
        }
      });
    } catch (e) {
      setState(() {
        _isLoadingBudgets = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load budgets: $e')),
        );
      }
    }
  }

  Future<void> _saveBudgetId(String budgetId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('budget_id', budgetId);
  }

  Future<void> _loadSavedBudgetId() async {
    final prefs = await SharedPreferences.getInstance();
    final savedBudgetId = prefs.getString('budget_id');

    if (savedBudgetId != null && _budgets.isNotEmpty) {
      final budgetIndex = _budgets.indexWhere((b) => b.id == savedBudgetId);

      if (budgetIndex != -1) {
        setState(() {
          _selectedBudgetId = savedBudgetId;
          _selectedBudgetName = _budgets[budgetIndex].name;
        });
        _updateScreens();
      } else {
        // If saved budget ID is not found in current budgets, select the first one
        setState(() {
          _selectedBudgetId = _budgets.first.id;
          _selectedBudgetName = _budgets.first.name;
        });
        _saveBudgetId(_budgets.first.id);
        _updateScreens();
      }
    }
  }

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
              if (_isLoadingBudgets)
                const Center(child: CircularProgressIndicator())
              else if (_budgets.isEmpty)
                const Center(child: Text('No budgets available'))
              else
                ...(_budgets.map((budget) => ListTile(
                      leading: Icon(
                        _selectedBudgetId == budget.id
                            ? Icons.radio_button_checked
                            : Icons.radio_button_unchecked,
                        color: const Color(0xFF0071BC),
                      ),
                      title: Text(budget.name),
                      onTap: () {
                        setState(() {
                          _selectedBudgetId = budget.id;
                          _selectedBudgetName = budget.name;
                        });
                        _saveBudgetId(budget.id);
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
                      const SnackBar(
                          content: Text('Create new budget - Coming soon!')),
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
        backgroundColor: const Color(0xFF0071BC),
        foregroundColor: Colors.white,
        title: GestureDetector(
          onTap: _showBudgetSelector,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  _selectedBudgetName,
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
            icon: const Icon(Icons.refresh),
            onPressed: _loadBudgets,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              // Clear all auth-related data including budget_id, keep base_url
              await prefs.remove('auth_token');
              await prefs.remove('user_email');
              await prefs.remove('budget_id');
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
        selectedItemColor: const Color(0xFF0071BC),
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
        backgroundColor: const Color(0xFF0071BC),
        foregroundColor: Colors.white,
        child: const Icon(Icons.add),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
    );
  }
}
