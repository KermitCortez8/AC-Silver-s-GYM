import AsyncStorage from '@react-native-async-storage/async-storage';

const USERS_KEY = 'gym_users';
const ATTENDANCE_KEY = 'gym_attendance';
const INVENTORY_KEY = 'gym_inventory';

let users = [];
let attendance = [];
let inventory = [];
let hydrated = false;

const parseStoredArray = (value) => {
  if (!value) {
    return [];
  }

  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
};

export const initializeStorage = async () => {
  if (hydrated) {
    return;
  }

  try {
    const entries = await AsyncStorage.multiGet([
      USERS_KEY,
      ATTENDANCE_KEY,
      INVENTORY_KEY,
    ]);
    const dataMap = new Map(entries);

    users = parseStoredArray(dataMap.get(USERS_KEY));
    attendance = parseStoredArray(dataMap.get(ATTENDANCE_KEY));
    inventory = parseStoredArray(dataMap.get(INVENTORY_KEY));
  } catch (error) {
    users = [];
    attendance = [];
    inventory = [];
  } finally {
    hydrated = true;
  }
};

const ensureHydrated = async () => {
  if (!hydrated) {
    await initializeStorage();
  }
};

const persistUsers = async () => {
  await AsyncStorage.setItem(USERS_KEY, JSON.stringify(users));
};

const persistAttendance = async () => {
  await AsyncStorage.setItem(ATTENDANCE_KEY, JSON.stringify(attendance));
};

const persistInventory = async () => {
  await AsyncStorage.setItem(INVENTORY_KEY, JSON.stringify(inventory));
};

// User Management
export const addUser = async (user) => {
  await ensureHydrated();
  const newUser = {
    id: Date.now().toString(),
    ...user,
    registrationDate: new Date().toISOString(),
  };
  users = [...users, newUser];
  await persistUsers();
  return newUser;
};

export const updateUser = async (id, updates) => {
  await ensureHydrated();
  const index = users.findIndex((user) => user.id === id);
  if (index !== -1) {
    users[index] = { ...users[index], ...updates };
    await persistUsers();
    return users[index];
  }
  return null;
};

export const deleteUser = async (id) => {
  await ensureHydrated();
  users = users.filter((user) => user.id !== id);
  await persistUsers();
};

export const getUsers = async () => {
  await ensureHydrated();
  return [...users];
};

export const getUserById = async (id) => {
  await ensureHydrated();
  return users.find((user) => user.id === id);
};

// Attendance Management
export const addAttendance = async (userId, userName) => {
  await ensureHydrated();
  const newAttendance = {
    id: Date.now().toString(),
    userId,
    userName,
    date: new Date().toISOString(),
    checkIn: new Date().toLocaleTimeString(),
  };
  attendance = [...attendance, newAttendance];
  await persistAttendance();
  return newAttendance;
};

export const getAttendance = async () => {
  await ensureHydrated();
  return [...attendance].reverse();
};

export const getAttendanceByDate = async (date) => {
  await ensureHydrated();
  return attendance.filter((record) => record.date.startsWith(date));
};

// Inventory Management
export const addInventoryItem = async (item) => {
  await ensureHydrated();
  const newItem = {
    id: Date.now().toString(),
    ...item,
    addedDate: new Date().toISOString(),
  };
  inventory = [...inventory, newItem];
  await persistInventory();
  return newItem;
};

export const updateInventoryItem = async (id, updates) => {
  await ensureHydrated();
  const index = inventory.findIndex((item) => item.id === id);
  if (index !== -1) {
    inventory[index] = { ...inventory[index], ...updates };
    await persistInventory();
    return inventory[index];
  }
  return null;
};

export const deleteInventoryItem = async (id) => {
  await ensureHydrated();
  inventory = inventory.filter((item) => item.id !== id);
  await persistInventory();
};

export const getInventory = async () => {
  await ensureHydrated();
  return [...inventory];
};

export const getInventoryItemById = async (id) => {
  await ensureHydrated();
  return inventory.find((item) => item.id === id);
};

// Statistics
export const getStats = async () => {
  await ensureHydrated();
  const today = new Date().toISOString().split('T')[0];

  return {
    totalUsers: users.length,
    totalAttendanceToday: attendance.filter((record) =>
      record.date.startsWith(today)
    ).length,
    totalInventoryItems: inventory.length,
    lowStockItems: inventory.filter((item) => item.quantity < 10).length,
  };
};
