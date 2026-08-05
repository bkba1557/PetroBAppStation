import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:nnexoris_customer/core/realtime/realtime_client.dart';
import 'package:nnexoris_customer/core/realtime/realtime_event.dart';

typedef SseAccessTokenReader = Future<String?> Function();

class NnexorisHttpSseClient implements RealtimeClient {
  NnexorisHttpSseClient({required this.uri, required this.accessToken});

  final Uri uri;
  final SseAccessTokenReader accessToken;
  final _events = StreamController<RealtimeEvent>.broadcast();
  final _states = StreamController<RealtimeConnectionState>.broadcast();
  final _gate = RealtimeSequenceGate();
  HttpClient? _http;
  StreamSubscription<String>? _lines;
  Timer? _retryTimer;
  bool _closed = false;
  bool _connecting = false;
  int _attempt = 0;
  int _lastEventId = 0;

  Uri get _httpUri => uri.replace(
        scheme: uri.scheme == 'wss'
            ? 'https'
            : uri.scheme == 'ws'
                ? 'http'
                : uri.scheme,
        queryParameters: {
          ...uri.queryParameters,
          if (_lastEventId > 0) 'after': '$_lastEventId',
        },
      );

  @override
  Future<void> connect() async {
    if (_connecting) return;
    _closed = false;
    _connecting = true;
    _states.add(_attempt == 0
        ? RealtimeConnectionState.connecting
        : RealtimeConnectionState.reconnecting);
    final client = HttpClient();
    _http = client;
    try {
      final request = await client.getUrl(_httpUri);
      request.headers.set(HttpHeaders.acceptHeader, 'text/event-stream');
      final token = await accessToken();
      if (token != null) {
        request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
      }
      if (_lastEventId > 0) {
        request.headers.set('Last-Event-ID', '$_lastEventId');
      }
      final response = await request.close();
      if (response.statusCode != HttpStatus.ok) {
        throw HttpException('Realtime HTTP ${response.statusCode}');
      }
      _attempt = 0;
      _retryTimer?.cancel();
      _states.add(RealtimeConnectionState.connected);
      String? eventId;
      String? data;
      _lines = response
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen(
        (line) {
          if (line.startsWith('id:')) eventId = line.substring(3).trim();
          if (line.startsWith('data:')) data = line.substring(5).trim();
          if (line.isEmpty && data != null) {
            try {
              final event = RealtimeEvent.fromJson(
                Map<String, dynamic>.from(jsonDecode(data!) as Map),
              );
              final parsedId = int.tryParse(eventId ?? '');
              if (parsedId != null && parsedId > _lastEventId) {
                _lastEventId = parsedId;
              }
              if (_gate.accept(event)) _events.add(event);
            } on Object {
              // Ignore malformed events; REST reconciliation remains authoritative.
            }
            eventId = null;
            data = null;
          }
        },
        onError: (_) => _reconnect(),
        onDone: _reconnect,
        cancelOnError: true,
      );
    } on Object {
      client.close(force: true);
      _reconnect();
    } finally {
      _connecting = false;
    }
  }

  void _reconnect() {
    if (_closed) return;
    _http?.close(force: true);
    _http = null;
    if (_retryTimer?.isActive == true) return;
    _states.add(RealtimeConnectionState.reconnecting);
    _attempt += 1;
    if (_attempt >= 5) _states.add(RealtimeConnectionState.polling);
    final boundedAttempt = _attempt > 5 ? 5 : _attempt;
    final seconds = 1 << boundedAttempt;
    _retryTimer = Timer(Duration(seconds: seconds), () async {
      if (_closed) return;
      await connect();
    });
  }

  @override
  Stream<RealtimeEvent> events({String? sessionId}) => _events.stream.where(
        (event) => sessionId == null || event.entityId == sessionId,
      );

  @override
  Stream<RealtimeConnectionState> get connectionStates => _states.stream;

  @override
  Future<void> disconnect() async {
    _closed = true;
    _retryTimer?.cancel();
    await _lines?.cancel();
    _http?.close(force: true);
    _states.add(RealtimeConnectionState.disconnected);
  }
}
