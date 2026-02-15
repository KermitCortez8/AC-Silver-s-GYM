import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Modal,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import colors from '../constants/colors';
import Card from '../components/Card';
import Button from '../components/Button';
import { addAttendance, getAttendance, getUsers } from '../data/storage';

const AttendanceScreen = () => {
  const [attendance, setAttendance] = useState([]);
  const [users, setUsers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    setAttendance(getAttendance());
    setUsers(getUsers());
  };

  const handleCheckIn = (user) => {
    addAttendance(user.id, user.name);
    loadData();
    setModalVisible(false);
    Alert.alert('Éxito', `${user.name} registrado correctamente`);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  const AttendanceCard = ({ record }) => (
    <Card style={styles.attendanceCard}>
      <View style={styles.attendanceHeader}>
        <View style={styles.checkInIcon}>
          <Ionicons name="checkmark-circle" size={28} color={colors.success} />
        </View>
        <View style={styles.attendanceInfo}>
          <Text style={styles.attendanceName}>{record.userName}</Text>
          <View style={styles.attendanceDetails}>
            <Ionicons name="calendar-outline" size={14} color={colors.textLight} />
            <Text style={styles.attendanceDate}>{formatDate(record.date)}</Text>
            <Ionicons
              name="time-outline"
              size={14}
              color={colors.textLight}
              style={styles.timeIcon}
            />
            <Text style={styles.attendanceTime}>{record.checkIn}</Text>
          </View>
        </View>
      </View>
    </Card>
  );

  const UserSelectCard = ({ user, onPress }) => (
    <TouchableOpacity
      style={styles.userSelectCard}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.userAvatar}>
        <Ionicons name="person" size={24} color={colors.white} />
      </View>
      <View style={styles.userSelectInfo}>
        <Text style={styles.userSelectName}>{user.name}</Text>
        {user.membershipType && (
          <Text style={styles.userSelectMembership}>{user.membershipType}</Text>
        )}
      </View>
      <Ionicons name="chevron-forward" size={24} color={colors.gray} />
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Control de Asistencia</Text>
        <Text style={styles.headerSubtitle}>
          {attendance.length} registros totales
        </Text>
      </View>

      <ScrollView style={styles.content}>
        {attendance.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="clipboard-outline" size={64} color={colors.gray} />
            <Text style={styles.emptyText}>No hay registros de asistencia</Text>
            <Text style={styles.emptySubtext}>
              Presiona el botón + para registrar entrada
            </Text>
          </View>
        ) : (
          attendance.map((record) => (
            <AttendanceCard key={record.id} record={record} />
          ))
        )}
      </ScrollView>

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setModalVisible(true)}
      >
        <Ionicons name="add" size={32} color={colors.white} />
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Registrar Entrada</Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              {users.length === 0 ? (
                <View style={styles.emptyUsers}>
                  <Ionicons name="people-outline" size={48} color={colors.gray} />
                  <Text style={styles.emptyUsersText}>
                    No hay usuarios registrados
                  </Text>
                  <Text style={styles.emptyUsersSubtext}>
                    Primero debes registrar usuarios en la sección de Gestión de
                    Usuarios
                  </Text>
                  <Button
                    title="Cerrar"
                    onPress={() => setModalVisible(false)}
                    variant="secondary"
                    style={styles.closeButton}
                  />
                </View>
              ) : (
                <>
                  <Text style={styles.modalInstructions}>
                    Selecciona el usuario para registrar su entrada:
                  </Text>
                  {users.map((user) => (
                    <UserSelectCard
                      key={user.id}
                      user={user}
                      onPress={() => handleCheckIn(user)}
                    />
                  ))}
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    backgroundColor: colors.success,
    padding: 20,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.white,
  },
  headerSubtitle: {
    fontSize: 14,
    color: colors.white,
    opacity: 0.9,
    marginTop: 4,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  attendanceCard: {
    marginBottom: 12,
  },
  attendanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkInIcon: {
    marginRight: 12,
  },
  attendanceInfo: {
    flex: 1,
  },
  attendanceName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
  },
  attendanceDetails: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  attendanceDate: {
    fontSize: 14,
    color: colors.textLight,
    marginLeft: 4,
  },
  timeIcon: {
    marginLeft: 12,
  },
  attendanceTime: {
    fontSize: 14,
    color: colors.textLight,
    marginLeft: 4,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.success,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text,
  },
  modalBody: {
    padding: 20,
  },
  modalInstructions: {
    fontSize: 14,
    color: colors.textLight,
    marginBottom: 16,
  },
  userSelectCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  userAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.success,
    justifyContent: 'center',
    alignItems: 'center',
  },
  userSelectInfo: {
    flex: 1,
    marginLeft: 12,
  },
  userSelectName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  userSelectMembership: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 2,
  },
  emptyUsers: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyUsersText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginTop: 16,
  },
  emptyUsersSubtext: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  closeButton: {
    marginTop: 20,
  },
});

export default AttendanceScreen;
