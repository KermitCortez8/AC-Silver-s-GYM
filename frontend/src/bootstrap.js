/** Ensambla las capacidades externas antes de montar Vue. */
import { configureApplicationServices } from './application/ports/services.js';
import * as http from './infrastructure/services/apiClient.js';
import { parseError, parseResponse } from './infrastructure/services/apiResponse.js';
import * as auth from './infrastructure/services/authService.js';
import * as session from './infrastructure/services/sessionStorage.js';
import * as attendance from './infrastructure/services/attendanceService.js';
import * as images from './infrastructure/services/storeImageService.js';
import * as storage from './infrastructure/config/publicStorage.js';
import * as preferences from './infrastructure/services/browserPreferences.js';
import { createUsersRepository } from './infrastructure/repositories/usersRepository.js';
import { createGymSettingsRepository } from './infrastructure/repositories/gymSettingsRepository.js';
import { APP_CONFIG } from './infrastructure/config/appConfig.js';
import { GOOGLE_CONFIG } from './infrastructure/config/googleConfig.js';

import { createAttendanceRepository } from './infrastructure/repositories/attendanceRepository.js';
import { createClientsRepository } from './infrastructure/repositories/clientsRepository.js';
import { createInventoryRepository } from './infrastructure/repositories/inventoryRepository.js';
import { createMembershipsRepository } from './infrastructure/repositories/membershipsRepository.js';
import { createSchedulesRepository } from './infrastructure/repositories/schedulesRepository.js';
import { createStoreRepository } from './infrastructure/repositories/storeRepository.js';

configureApplicationServices({
  http: { ...http, parseError, parseResponse },
  auth, session, attendance, images, storage, preferences,
  config: { app: APP_CONFIG, google: GOOGLE_CONFIG },
  repositories: {
    users: createUsersRepository(http),
    attendance: createAttendanceRepository(http, APP_CONFIG.authApiBaseUrl),
    clients: createClientsRepository(http, APP_CONFIG.authApiBaseUrl),
    inventory: createInventoryRepository(http, APP_CONFIG.authApiBaseUrl),
    memberships: createMembershipsRepository(http, APP_CONFIG.authApiBaseUrl),
    schedules: createSchedulesRepository(http, APP_CONFIG.authApiBaseUrl),
    store: createStoreRepository(http, APP_CONFIG.authApiBaseUrl),

    gymSettings: createGymSettingsRepository(http),
  },
});
