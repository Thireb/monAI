import "database/app_database.dart";
import "repositories/budget_repository.dart";
import "repositories/category_repository.dart";
import "repositories/expense_repository.dart";
import "repositories/tag_repository.dart";
import "services/budget_sync_service.dart";
import "services/mobile_budget_api_client.dart";
import "services/secure_token_store.dart";
import "services/settings_service.dart";
import "services/sync_service.dart";

/// App-wide dependencies (initialized in [bootstrapApp]).
class AppScope {
  AppScope._();

  static final SecureTokenStore tokens = SecureTokenStore();
  static late SettingsService settings;
  static late MobileBudgetApiClient mobileApi;
  static late BudgetRepository budgetRepo;
  static late CategoryRepository categoryRepo;
  static late TagRepository tagRepo;
  static late ExpenseRepository expenseRepo;
  static late BudgetSyncService budgetSync;
  static late SyncService syncService;

  static Future<void> init() async {
    settings = await SettingsService.create();
    mobileApi = MobileBudgetApiClient(settings, tokens);
    final db = AppDatabase.instance;
    budgetRepo = BudgetRepository(db);
    categoryRepo = CategoryRepository(db);
    tagRepo = TagRepository(db);
    expenseRepo = ExpenseRepository(db);
    budgetSync = BudgetSyncService(
      mobileApi,
      budgetRepo,
      categoryRepo,
      tagRepo,
      expenseRepo,
    );
    syncService = SyncService(settings, mobileApi);
  }
}
