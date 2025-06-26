import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'budget_tabs_screen.dart';
import 'package:flutter_svg/flutter_svg.dart';

void main() {
  runApp(const EnvelopeBudgetApp());
}

class EnvelopeBudgetApp extends StatelessWidget {
  const EnvelopeBudgetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EnvelopeBudget',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0071BC), // Your logo blue
          primary: const Color(0xFF0071BC),
          secondary: const Color(0xFF666666), // Your logo gray
        ),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0071BC),
          foregroundColor: Colors.white,
        ),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: Color(0xFF0071BC),
          foregroundColor: Colors.white,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF0071BC),
            foregroundColor: Colors.white,
          ),
        ),
      ),
      home: const AuthCheckScreen(),
    );
  }
}

// Add this new screen to check authentication status
class AuthCheckScreen extends StatefulWidget {
  const AuthCheckScreen({super.key});

  @override
  State<AuthCheckScreen> createState() => _AuthCheckScreenState();
}

class _AuthCheckScreenState extends State<AuthCheckScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final authToken = prefs.getString('auth_token');

    // Add a small delay to show the splash screen briefly
    await Future.delayed(const Duration(milliseconds: 1000));

    if (mounted) {
      if (authToken != null && authToken.isNotEmpty) {
        // User is logged in, go to budget tabs
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const BudgetTabsScreen()),
        );
      } else {
        // User is not logged in, go to login screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const LoginScreen()),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              height: 120,
              width: 120,
              margin: const EdgeInsets.only(bottom: 24),
              child: SvgPicture.asset(
                'assets/images/eb-logo.svg',
                height: 120,
                width: 120,
              ),
            ),
            // App title
            Text(
              'EnvelopeBudget',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF0071BC),
                  ),
            ),
            const SizedBox(height: 32),
            // Loading indicator
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0071BC)),
            ),
          ],
        ),
      ),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _baseUrlController =
      TextEditingController(text: 'https://envelopebudget.com');

  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _showAdvancedSettings = false;

  @override
  void initState() {
    super.initState();
    _loadSavedBaseUrl();
  }

  Future<void> _loadSavedBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final savedBaseUrl =
        prefs.getString('base_url') ?? 'https://envelopebudget.com';
    setState(() {
      _baseUrlController.text = savedBaseUrl;
    });
  }

  Future<void> _saveBaseUrl() async {
    // Only save if URL is valid
    final url = _baseUrlController.text;
    final uri = Uri.tryParse(url);

    if (uri != null && uri.host.isNotEmpty && uri.scheme.startsWith('http')) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('base_url', url);
    }
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      await _saveBaseUrl();
      print('Saving base URL...');

      final baseUrl = _baseUrlController.text;
      print('Using base URL: $baseUrl');

      print('Sending login request to $baseUrl/api/auth/login...');
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/login'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': _emailController.text.trim(),
          'password': _passwordController.text,
        }),
      );
      print('Response status code: ${response.statusCode}');
      print('Response body: ${response.body}');

      if (response.statusCode == 200) {
        print('Login successful, parsing response data...');
        final responseData = jsonDecode(response.body);

        // Save authentication token
        print('Saving auth token and user email...');
        final prefs = await SharedPreferences.getInstance();
        final authToken = responseData['token'] ?? '';
        await prefs.setString('auth_token', authToken);
        await prefs.setString('user_email', _emailController.text.trim());

        // Fetch user's budgets and save the first budget ID
        print('Fetching user budgets...');
        try {
          final budgetsResponse = await http.get(
            Uri.parse('${_baseUrlController.text}/api/budgets'),
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $authToken',
            },
          );

          if (budgetsResponse.statusCode == 200) {
            final List<dynamic> budgets = jsonDecode(budgetsResponse.body);
            if (budgets.isNotEmpty) {
              final budgetId = budgets[0]['id'] as String;
              await prefs.setString('budget_id', budgetId);
              print('Saved budget ID: $budgetId');
            }
          } else {
            print('Failed to fetch budgets: ${budgetsResponse.statusCode}');
          }
        } catch (e) {
          print('Error fetching budgets: $e');
          // Continue with login even if budget fetch fails
        }

        if (mounted) {
          print('Showing success message and navigating...');
          _showSuccessMessage('Login successful!');
          // Navigate to budget tabs screen
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const BudgetTabsScreen()),
          );
        }
      } else {
        print('Login failed with status code: ${response.statusCode}');
        final errorData = jsonDecode(response.body);
        _showErrorMessage(errorData['message'] ?? 'Login failed');
      }
    } catch (e) {
      _showErrorMessage('Network error: ${e.toString()}');
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
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

  void _showSuccessMessage(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: const Color(0xFF0071BC),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Add some top padding to center content when keyboard is closed
                SizedBox(height: MediaQuery.of(context).size.height * 0.1),

                // Logo
                Container(
                  height: 120,
                  width: 120,
                  margin: const EdgeInsets.only(bottom: 24),
                  child: SvgPicture.asset(
                    'assets/images/eb-logo.svg',
                    height: 120,
                    width: 120,
                  ),
                ),

                // Title
                Text(
                  'EnvelopeBudget',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: const Color(0xFF0071BC),
                      ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 48),

                // Email field
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  onFieldSubmitted: (_) => _login(),
                  decoration: InputDecoration(
                    labelText: 'Email',
                    prefixIcon:
                        const Icon(Icons.email, color: Color(0xFF0071BC)),
                    border: const OutlineInputBorder(),
                    focusedBorder: const OutlineInputBorder(
                      borderSide:
                          BorderSide(color: Color(0xFF0071BC), width: 2),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your email';
                    }
                    if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$')
                        .hasMatch(value)) {
                      return 'Please enter a valid email';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Password field
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  onFieldSubmitted: (_) => _login(),
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon:
                        const Icon(Icons.lock, color: Color(0xFF0071BC)),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility
                            : Icons.visibility_off,
                        color: const Color(0xFF666666),
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                    border: const OutlineInputBorder(),
                    focusedBorder: const OutlineInputBorder(
                      borderSide:
                          BorderSide(color: Color(0xFF0071BC), width: 2),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please enter your password';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // Login button
                ElevatedButton(
                  onPressed: _isLoading ? null : _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0071BC),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : const Text('Login',
                          style: TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(height: 16),

                // Advanced settings toggle
                TextButton(
                  onPressed: () {
                    setState(() {
                      _showAdvancedSettings = !_showAdvancedSettings;
                    });
                  },
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _showAdvancedSettings
                            ? Icons.expand_less
                            : Icons.expand_more,
                        color: const Color(0xFF666666),
                      ),
                      Text(
                        'Server Settings',
                        style: TextStyle(color: const Color(0xFF666666)),
                      ),
                    ],
                  ),
                ),

                // Advanced settings
                if (_showAdvancedSettings) ...[
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _baseUrlController,
                    decoration: const InputDecoration(
                      labelText: 'Server URL',
                      prefixIcon: Icon(Icons.cloud, color: Color(0xFF0071BC)),
                      border: OutlineInputBorder(),
                      focusedBorder: OutlineInputBorder(
                        borderSide:
                            BorderSide(color: Color(0xFF0071BC), width: 2),
                      ),
                      helperText: 'e.g., https://budget.example.com',
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter a server URL';
                      }
                      final uri = Uri.tryParse(value);

                      if (uri == null ||
                          uri.host.isEmpty ||
                          (!uri.scheme.startsWith('http'))) {
                        return 'Please enter a valid URL (must start with http:// or https://)';
                      }
                      return null;
                    },
                  ),
                ],

                // Add bottom padding to ensure content is accessible
                const SizedBox(height: 50),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _baseUrlController.dispose();
    super.dispose();
  }
}

// Add this helper function at the top level (outside of classes)
Future<void> logout(BuildContext context) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove('auth_token');
  await prefs.remove('user_email');
  await prefs.remove('budget_id');

  if (context.mounted) {
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (context) => const LoginScreen()),
      (route) => false,
    );
  }
}
