import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import {
  createDrawerNavigator,
  DrawerContentScrollView,
  DrawerItemList,
} from '@react-navigation/drawer';
import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import colors from '../constants/colors';

// Import screens
import HomeScreen from '../screens/HomeScreen';
import UsersScreen from '../screens/UsersScreen';
import AttendanceScreen from '../screens/AttendanceScreen';
import InventoryScreen from '../screens/InventoryScreen';

const Drawer = createDrawerNavigator();

const CustomDrawerContent = ({ isWide, ...props }) => (
  <DrawerContentScrollView
    {...props}
    contentContainerStyle={styles.drawerScroll}
  >
    <View style={styles.brandSection}>
      <Text style={styles.brandTitle}>AC Silver's GYM</Text>
      <Text style={styles.brandSubtitle}>Panel de Control</Text>
    </View>

    <View style={styles.drawerSection}>
      <DrawerItemList {...props} />
    </View>

    {isWide && (
      <View style={styles.drawerFooter}>
        <Text style={styles.footerText}>Dashboard v1.0</Text>
      </View>
    )}
  </DrawerContentScrollView>
);

const AppNavigator = () => {
  const { width } = useWindowDimensions();
  const isWide = width >= 1024;

  return (
    <NavigationContainer>
      <Drawer.Navigator
        drawerContent={(props) => (
          <CustomDrawerContent {...props} isWide={isWide} />
        )}
        screenOptions={({ route }) => ({
          headerShown: !isWide,
          drawerType: isWide ? 'permanent' : 'front',
          overlayColor: isWide ? 'transparent' : undefined,
          drawerStyle: [styles.drawer, isWide && styles.drawerPermanent],
          sceneContainerStyle: styles.sceneContainer,
          drawerActiveTintColor: colors.white,
          drawerInactiveTintColor: colors.gray,
          drawerActiveBackgroundColor: colors.primary,
          drawerLabelStyle: styles.drawerLabel,
          drawerIcon: ({ color, size }) => {
            let iconName;

            if (route.name === 'Home') {
              iconName = 'home';
            } else if (route.name === 'Users') {
              iconName = 'people';
            } else if (route.name === 'Attendance') {
              iconName = 'checkmark-circle';
            } else if (route.name === 'Inventory') {
              iconName = 'cube';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
        })}
      >
        <Drawer.Screen
          name="Home"
          component={HomeScreen}
          options={{
            drawerLabel: 'Inicio',
          }}
        />
        <Drawer.Screen
          name="Users"
          component={UsersScreen}
          options={{
            drawerLabel: 'Usuarios',
          }}
        />
        <Drawer.Screen
          name="Attendance"
          component={AttendanceScreen}
          options={{
            drawerLabel: 'Asistencia',
          }}
        />
        <Drawer.Screen
          name="Inventory"
          component={InventoryScreen}
          options={{
            drawerLabel: 'Inventario',
          }}
        />
      </Drawer.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  drawer: {
    backgroundColor: colors.dark,
    borderRightWidth: 1,
    borderRightColor: colors.dark,
    width: 260,
  },
  drawerPermanent: {
    paddingTop: 12,
  },
  drawerLabel: {
    marginLeft: -12,
    fontSize: 14,
    fontWeight: '600',
  },
  drawerScroll: {
    flex: 1,
    paddingTop: 0,
  },
  brandSection: {
    paddingVertical: 28,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2a3a',
  },
  brandTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.white,
  },
  brandSubtitle: {
    fontSize: 12,
    color: colors.gray,
    marginTop: 4,
  },
  drawerSection: {
    paddingVertical: 12,
  },
  drawerFooter: {
    marginTop: 'auto',
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  footerText: {
    fontSize: 12,
    color: colors.gray,
  },
  sceneContainer: {
    backgroundColor: colors.background,
  },
});

export default AppNavigator;
