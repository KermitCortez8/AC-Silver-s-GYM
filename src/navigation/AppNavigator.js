import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import colors from '../constants/colors';

// Import screens
import HomeScreen from '../screens/HomeScreen';
import UsersScreen from '../screens/UsersScreen';
import AttendanceScreen from '../screens/AttendanceScreen';
import InventoryScreen from '../screens/InventoryScreen';

const Tab = createBottomTabNavigator();

const AppNavigator = () => {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === 'Home') {
              iconName = focused ? 'home' : 'home-outline';
            } else if (route.name === 'Users') {
              iconName = focused ? 'people' : 'people-outline';
            } else if (route.name === 'Attendance') {
              iconName = focused ? 'checkmark-circle' : 'checkmark-circle-outline';
            } else if (route.name === 'Inventory') {
              iconName = focused ? 'cube' : 'cube-outline';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: colors.primary,
          tabBarInactiveTintColor: colors.gray,
          tabBarStyle: {
            paddingBottom: 5,
            paddingTop: 5,
            height: 60,
            borderTopWidth: 1,
            borderTopColor: colors.border,
          },
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '600',
          },
          headerShown: false,
        })}
      >
        <Tab.Screen
          name="Home"
          component={HomeScreen}
          options={{
            tabBarLabel: 'Inicio',
          }}
        />
        <Tab.Screen
          name="Users"
          component={UsersScreen}
          options={{
            tabBarLabel: 'Usuarios',
          }}
        />
        <Tab.Screen
          name="Attendance"
          component={AttendanceScreen}
          options={{
            tabBarLabel: 'Asistencia',
          }}
        />
        <Tab.Screen
          name="Inventory"
          component={InventoryScreen}
          options={{
            tabBarLabel: 'Inventario',
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
