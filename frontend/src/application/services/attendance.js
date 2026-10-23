import { getApplicationServices } from '../ports/services.js';

export const attendanceGet = (...args) => getApplicationServices().attendance.attendanceGet(...args);
export const attendanceEntry = (...args) => getApplicationServices().attendance.attendanceEntry(...args);
export const generalAttendanceEntry = (...args) => getApplicationServices().attendance.generalAttendanceEntry(...args);
export const attendanceExit = (...args) => getApplicationServices().attendance.attendanceExit(...args);
export const attendanceCorrect = (...args) => getApplicationServices().attendance.attendanceCorrect(...args);
export const attendanceAnnul = (...args) => getApplicationServices().attendance.attendanceAnnul(...args);
