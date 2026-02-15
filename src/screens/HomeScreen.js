import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import colors from '../constants/colors';
import Card from '../components/Card';
import { getStats } from '../data/storage';

const HomeScreen = ({ navigation }) => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalAttendanceToday: 0,
    totalInventoryItems: 0,
    lowStockItems: 0,
  });

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      void refreshStats();
    });

    void refreshStats();

    return unsubscribe;
  }, [navigation]);

  const refreshStats = async () => {
    const nextStats = await getStats();
    setStats(nextStats);
  };

  const StatCard = ({ icon, title, value, color, onPress }) => (
    <TouchableOpacity 
      style={[styles.statCard, { borderLeftColor: color }]} 
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Ionicons name={icon} size={32} color={color} />
      <View style={styles.statInfo}>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statTitle}>{title}</Text>
      </View>
    </TouchableOpacity>
  );

  const MenuCard = ({ icon, title, description, onPress, color }) => (
    <Card style={styles.menuCard} onPress={onPress}>
      <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={32} color={color} />
      </View>
      <View style={styles.menuInfo}>
        <Text style={styles.menuTitle}>{title}</Text>
        <Text style={styles.menuDescription}>{description}</Text>
      </View>
      <Ionicons name="chevron-forward" size={24} color={colors.gray} />
    </Card>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>AC Silver's GYM</Text>
        <Text style={styles.subtitle}>Sistema de Gestión</Text>
      </View>

      <View style={styles.statsContainer}>
        <StatCard
          icon="people"
          title="Usuarios"
          value={stats.totalUsers}
          color={colors.primary}
          onPress={() => navigation.navigate('Users')}
        />
        <StatCard
          icon="checkmark-circle"
          title="Asistencia Hoy"
          value={stats.totalAttendanceToday}
          color={colors.success}
          onPress={() => navigation.navigate('Attendance')}
        />
      </View>

      <View style={styles.statsContainer}>
        <StatCard
          icon="cube"
          title="Inventario"
          value={stats.totalInventoryItems}
          color={colors.accent}
          onPress={() => navigation.navigate('Inventory')}
        />
        <StatCard
          icon="warning"
          title="Stock Bajo"
          value={stats.lowStockItems}
          color={colors.danger}
          onPress={() => navigation.navigate('Inventory')}
        />
      </View>

      <View style={styles.menuSection}>
        <Text style={styles.sectionTitle}>Acceso Rápido</Text>
        
        <MenuCard
          icon="person-add"
          title="Gestión de Usuarios"
          description="Registrar y administrar miembros"
          color={colors.primary}
          onPress={() => navigation.navigate('Users')}
        />

        <MenuCard
          icon="calendar"
          title="Control de Asistencia"
          description="Registrar entrada y salida"
          color={colors.success}
          onPress={() => navigation.navigate('Attendance')}
        />

        <MenuCard
          icon="grid"
          title="Gestión de Inventario"
          description="Administrar equipamiento y productos"
          color={colors.accent}
          onPress={() => navigation.navigate('Inventory')}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    padding: 20,
    paddingTop: 40,
    backgroundColor: colors.primary,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.white,
  },
  subtitle: {
    fontSize: 16,
    color: colors.white,
    opacity: 0.9,
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 10,
    gap: 10,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statInfo: {
    marginLeft: 12,
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  statTitle: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 2,
  },
  menuSection: {
    padding: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
    marginVertical: 12,
    marginLeft: 8,
  },
  menuCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuInfo: {
    flex: 1,
    marginLeft: 16,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  menuDescription: {
    fontSize: 13,
    color: colors.textLight,
    marginTop: 2,
  },
});

export default HomeScreen;
