import { getActivePinia } from "pinia";
import { getApplicationServices } from "../ports/services.js";
import { inCurrentSession } from "./sessionBoundary.js";

export const useAttendance = () => {
  const pinia = getActivePinia();
  const { attendance } = getApplicationServices(pinia);
  return Object.fromEntries(
    Object.entries(attendance).map(([name, operation]) => [
      name,
      (...args) => inCurrentSession(() => operation(...args), pinia),
    ]),
  );
};
