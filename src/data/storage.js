// Data storage utilities using AsyncStorage for future backend integration
import { Alert } from 'react-native';

// Simulated storage (in-memory for now, can be replaced with AsyncStorage or backend API)
let users = [];
let attendance = [];
let inventory = [];

// User Management
export const addUser = (user) => {
  const newUser = {
    id: Date.now().toString(),
    ...user,
    registrationDate: new Date().toISOString(),
  };
  users.push(newUser);
  return newUser;
};

export const updateUser = (id, updates) => {
  const index = users.findIndex(u => u.id === id);
  if (index !== -1) {
    users[index] = { ...users[index], ...updates };
    return users[index];
  }
  return null;
};

export const deleteUser = (id) => {
  users = users.filter(u => u.id !== id);
};

export const getUsers = () => {
  return [...users];
};

export const getUserById = (id) => {
  return users.find(u => u.id === id);
};

// Attendance Management
export const addAttendance = (userId, userName) => {
  const newAttendance = {
    id: Date.now().toString(),
    userId,
    userName,
    date: new Date().toISOString(),
    checkIn: new Date().toLocaleTimeString(),
  };
  attendance.push(newAttendance);
  return newAttendance;
};

export const getAttendance = () => {
  return [...attendance].reverse();
};

export const getAttendanceByDate = (date) => {
  return attendance.filter(a => a.date.startsWith(date));
};

// Inventory Management
export const addInventoryItem = (item) => {
  const newItem = {
    id: Date.now().toString(),
    ...item,
    addedDate: new Date().toISOString(),
  };
  inventory.push(newItem);
  return newItem;
};

export const updateInventoryItem = (id, updates) => {
  const index = inventory.findIndex(i => i.id === id);
  if (index !== -1) {
    inventory[index] = { ...inventory[index], ...updates };
    return inventory[index];
  }
  return null;
};

export const deleteInventoryItem = (id) => {
  inventory = inventory.filter(i => i.id !== id);
};

export const getInventory = () => {
  return [...inventory];
};

export const getInventoryItemById = (id) => {
  return inventory.find(i => i.id === id);
};

// Statistics
export const getStats = () => {
  return {
    totalUsers: users.length,
    totalAttendanceToday: attendance.filter(a => 
      a.date.startsWith(new Date().toISOString().split('T')[0])
    ).length,
    totalInventoryItems: inventory.length,
    lowStockItems: inventory.filter(i => i.quantity < 10).length,
  };
};
