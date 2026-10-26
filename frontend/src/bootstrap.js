/** Ensambla las capacidades externas antes de montar Vue. */
import { configureApplicationServices } from "./application/ports/services.js";
import { createApiClient } from "./infrastructure/services/apiClient.js";
import {
  parseError,
  parseResponse,
} from "./infrastructure/services/apiResponse.js";
import { createAuthService } from "./infrastructure/services/authService.js";
import * as session from "./infrastructure/services/sessionStorage.js";
import { createAttendanceService } from "./infrastructure/services/attendanceService.js";
import { createStoreImageService } from "./infrastructure/services/storeImageService.js";
import * as storage from "./infrastructure/config/publicStorage.js";
import * as preferences from "./infrastructure/services/browserPreferences.js";
import { createUsersRepository } from "./infrastructure/repositories/usersRepository.js";
import { createGymSettingsRepository } from "./infrastructure/repositories/gymSettingsRepository.js";
import { APP_CONFIG } from "./infrastructure/config/appConfig.js";
import { GOOGLE_CONFIG } from "./infrastructure/config/googleConfig.js";

import { createAttendanceRepository } from "./infrastructure/repositories/attendanceRepository.js";
import { createClientsRepository } from "./infrastructure/repositories/clientsRepository.js";
import { createInventoryRepository } from "./infrastructure/repositories/inventoryRepository.js";
import { createMembershipsRepository } from "./infrastructure/repositories/membershipsRepository.js";
import { createSchedulesRepository } from "./infrastructure/repositories/schedulesRepository.js";
import { createStoreRepository } from "./infrastructure/repositories/storeRepository.js";

export const installServices = (pinia, overrides = {}) => {
  const config = {
    app: { ...APP_CONFIG, ...overrides.config?.app },
    google: { ...GOOGLE_CONFIG, ...overrides.config?.google },
  };
  const http = overrides.http || {
    ...createApiClient(config.app),
    parseError,
    parseResponse,
  };
  const assets = overrides.storage || storage;
  return configureApplicationServices(
    {
      http,
      config,
      storage: assets,
      auth: overrides.auth || createAuthService(http),
      attendance: overrides.attendance || createAttendanceService(http),
      images:
        overrides.images ||
        createStoreImageService(config.app, assets.storeImageUrl),
      session: overrides.session || session,
      preferences: overrides.preferences || preferences,
      repositories: overrides.repositories || {
        users: createUsersRepository(http),
        attendance: createAttendanceRepository(http, config.app.authApiBaseUrl),
        clients: createClientsRepository(http, config.app.authApiBaseUrl),
        inventory: createInventoryRepository(http, config.app.authApiBaseUrl),
        memberships: createMembershipsRepository(
          http,
          config.app.authApiBaseUrl,
        ),
        schedules: createSchedulesRepository(http, config.app.authApiBaseUrl),
        store: createStoreRepository(http, config.app.authApiBaseUrl),
        gymSettings: createGymSettingsRepository(http),
      },
    },
    pinia,
  );
};
