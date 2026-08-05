class ApiResponse<T> {
  const ApiResponse({
    required this.data,
    this.correlationId,
    this.eventVersion,
  });

  final T data;
  final String? correlationId;
  final int? eventVersion;
}
