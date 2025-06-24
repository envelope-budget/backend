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
      EnvelopesScreen(
        key: ValueKey(_selectedBudgetId),
        budgetId: _selectedBudgetId,
      ),
      const TransactionsScreen(),
    ];
    _loadBudgets().then((_) => _loadSavedBudgetId());
  }

  void _updateScreens() {
    setState(() {
      _screens = [
        EnvelopesScreen(
          key: ValueKey(_selectedBudgetId),
          budgetId: _selectedBudgetId,
        ),
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
        setState(() {
          _selectedBudgetId = _budgets.first.id;
          _selectedBudgetName = _budgets.first.name;
        });
        _saveBudgetId(_budgets.first.id);
        _updateScreens();
      }
    }
  }

  void _showBudgetDrawer() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (BuildContext context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          minChildSize: 0.3,
          maxChildSize: 0.9,
          builder: (context, scrollController) {
            return Container(
              decoration: const BoxDecoration(
                borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
              ),
              child: Column(
                children: [
                  Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.symmetric(vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Text(
                          'Select Budget',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const Spacer(),
                        IconButton(
                          onPressed: () => Navigator.pop(context),
                          icon: const Icon(Icons.close),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: _isLoadingBudgets
                        ? const Center(child: CircularProgressIndicator())
                        : _budgets.isEmpty
                            ? const Center(child: Text('No budgets available'))
                            : ListView.builder(
                                controller: scrollController,
                                itemCount:
                                    _budgets.length + 1, // +1 for create button
                                itemBuilder: (context, index) {
                                  if (index == _budgets.length) {
                                    return Padding(
                                      padding: const EdgeInsets.all(16),
                                      child: OutlinedButton.icon(
                                        onPressed: () {
                                          Navigator.pop(context);
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(
                                            const SnackBar(
                                                content: Text(
                                                    'Create new budget - Coming soon!')),
                                          );
                                        },
                                        icon: const Icon(Icons.add),
                                        label: const Text('Create New Budget'),
                                        style: OutlinedButton.styleFrom(
                                          padding: const EdgeInsets.symmetric(
                                              vertical: 12),
                                        ),
                                      ),
                                    );
                                  }

                                  final budget = _budgets[index];
                                  final isSelected =
                                      _selectedBudgetId == budget.id;

                                  return ListTile(
                                    leading: Icon(
                                      isSelected
                                          ? Icons.radio_button_checked
                                          : Icons.radio_button_unchecked,
                                      color: const Color(0xFF0071BC),
                                    ),
                                    title: Text(budget.name),
                                    selected: isSelected,
                                    onTap: () {
                                      setState(() {
                                        _selectedBudgetId = budget.id;
                                        _selectedBudgetName = budget.name;
                                      });
                                      _saveBudgetId(budget.id);
                                      _updateScreens();
                                      Navigator.pop(context);
                                    },
                                  );
                                },
                              ),
                  ),
                ],
              ),
            );
          },
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
        toolbarHeight: 56, // Compact height
        title: GestureDetector(
          onTap: _showBudgetDrawer,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  _selectedBudgetName,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 16), // Slightly smaller
                ),
              ),
              const SizedBox(width: 4),
              const Icon(Icons.keyboard_arrow_down, size: 20),
            ],
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: _loadBudgets,
            tooltip: 'Refresh',
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, size: 20),
            onSelected: (value) async {
              if (value == 'logout') {
                final prefs = await SharedPreferences.getInstance();
                await prefs.remove('auth_token');
                await prefs.remove('user_email');
                await prefs.remove('budget_id');
                if (mounted) {
                  Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                        builder: (context) => const LoginScreen()),
                  );
                }
              }
            },
            itemBuilder: (BuildContext context) => [
              const PopupMenuItem<String>(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, size: 18),
                    SizedBox(width: 8),
                    Text('Logout'),
                  ],
                ),
              ),
            ],
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
        type: BottomNavigationBarType.fixed,
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
