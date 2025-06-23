import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class Budget {
  final String id;
  final String name;
  final String dateFormat;
  final String currencyIsoCode;
  final int currencyDecimalDigits;
  final String currencyDecimalSeparator;
  final bool currencySymbolFirst;
  final String currencyGroupSeparator;
  final String currencySymbol;
  final bool currencyDisplaySymbol;

  Budget({
    required this.id,
    required this.name,
    required this.dateFormat,
    required this.currencyIsoCode,
    required this.currencyDecimalDigits,
    required this.currencyDecimalSeparator,
    required this.currencySymbolFirst,
    required this.currencyGroupSeparator,
    required this.currencySymbol,
    required this.currencyDisplaySymbol,
  });

  factory Budget.fromJson(Map<String, dynamic> json) {
    return Budget(
      id: json['id'],
      name: json['name'],
      dateFormat: json['date_format'],
      currencyIsoCode: json['currency_iso_code'],
      currencyDecimalDigits: json['currency_decimal_digits'],
      currencyDecimalSeparator: json['currency_decimal_separator'],
      currencySymbolFirst: json['currency_symbol_first'],
      currencyGroupSeparator: json['currency_group_separator'],
      currencySymbol: json['currency_symbol'],
      currencyDisplaySymbol: json['currency_display_symbol'],
    );
  }
}

class ApiService {
  static Future<String> _getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final baseUrl = prefs.getString('base_url') ?? '';
    print('Getting base URL: $baseUrl');
    return baseUrl;
  }

  static Future<String> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('auth_token') ?? '';
    print('Getting auth token: $token');
    return token;
  }

  static Future<List<Budget>> getBudgets() async {
    print('Fetching budgets...');
    final baseUrl = await _getBaseUrl();
    final token = await _getAuthToken();

    print('Making HTTP request to: $baseUrl/api/budgets');
    final response = await http.get(
      Uri.parse('$baseUrl/api/budgets'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );

    print('Response status code: ${response.statusCode}');
    if (response.statusCode == 200) {
      final List<dynamic> budgetsJson = json.decode(response.body);
      final budgets = budgetsJson.map((json) => Budget.fromJson(json)).toList();
      print('Successfully loaded ${budgets.length} budgets');
      return budgets;
    } else {
      print('Error loading budgets: ${response.statusCode}');
      throw Exception('Failed to load budgets: ${response.statusCode}');
    }
  }}
