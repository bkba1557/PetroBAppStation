enum AppEnvironment {
  development,
  staging,
  production;

  static AppEnvironment parse(String value) => switch (value.toLowerCase()) {
        'development' || 'dev' => development,
        'staging' || 'stage' => staging,
        'production' || 'prod' => production,
        _ => throw ArgumentError.value(value, 'APP_ENV', 'Unsupported environment'),
      };
}
