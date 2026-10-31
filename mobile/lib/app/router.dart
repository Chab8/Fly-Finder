import 'package:go_router/go_router.dart';

import '../features/catalog/catalog_screen.dart';
import '../features/catalog/detail_screens.dart';
import '../features/history/history_screen.dart';
import '../features/home/home_screen.dart';
import '../features/identify/analysis_screen.dart';
import '../features/identify/capture_screen.dart';
import '../features/results/result_screens.dart';
import '../models/identification.dart';

GoRouter buildRouter({String initialLocation = '/'}) => GoRouter(
      initialLocation: initialLocation,
      routes: [
        GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
        GoRoute(
          path: '/identify/:mode',
          builder: (_, state) => CaptureScreen(mode: IdentifyMode.parse(state.pathParameters['mode']!)),
          routes: [
            GoRoute(path: 'analysis', builder: (_, state) => AnalysisScreen(mode: IdentifyMode.parse(state.pathParameters['mode']!))),
            GoRoute(path: 'result', builder: (_, state) => LiveResultScreen(mode: IdentifyMode.parse(state.pathParameters['mode']!))),
          ],
        ),
        GoRoute(
          path: '/catalog',
          builder: (_, state) => CatalogScreen(initialTab: state.uri.queryParameters['tab'] == 'flies' ? 1 : 0),
        ),
        GoRoute(path: '/organisms/:id', builder: (_, state) => OrganismDetailScreen(id: state.pathParameters['id']!)),
        GoRoute(
          path: '/flies/:id',
          builder: (_, state) => FlyDetailScreen(id: state.pathParameters['id']!),
          routes: [GoRoute(path: 'products', builder: (_, state) => ProductsScreen(flyId: state.pathParameters['id']!))],
        ),
        GoRoute(path: '/history', builder: (_, _) => const HistoryScreen()),
        GoRoute(path: '/history/:id', builder: (_, state) => StoredResultScreen(id: state.pathParameters['id']!)),
      ],
    );
