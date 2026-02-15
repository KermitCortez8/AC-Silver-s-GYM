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
import Input from '../components/Input';
import { addUser, updateUser, deleteUser, getUsers } from '../data/storage';

const UsersScreen = ({ navigation }) => {
  const [users, setUsers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    membershipType: '',
  });

  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      void loadUsers();
    });

    void loadUsers();

    return unsubscribe;
  }, [navigation]);

  const loadUsers = async () => {
    const storedUsers = await getUsers();
    setUsers(storedUsers);
  };

  const openModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        name: user.name,
        email: user.email,
        phone: user.phone,
        membershipType: user.membershipType,
      });
    } else {
      setEditingUser(null);
      setFormData({
        name: '',
        email: '',
        phone: '',
        membershipType: '',
      });
    }
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setEditingUser(null);
    setFormData({
      name: '',
      email: '',
      phone: '',
      membershipType: '',
    });
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      Alert.alert('Error', 'Por favor ingresa el nombre');
      return;
    }

    if (editingUser) {
      await updateUser(editingUser.id, formData);
      Alert.alert('Éxito', 'Usuario actualizado correctamente');
    } else {
      await addUser(formData);
      Alert.alert('Éxito', 'Usuario registrado correctamente');
    }

    await loadUsers();
    closeModal();
  };

  const handleDelete = (id, name) => {
    Alert.alert(
      'Confirmar',
      `¿Estás seguro de eliminar a ${name}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            await deleteUser(id);
            await loadUsers();
            Alert.alert('Éxito', 'Usuario eliminado');
          },
        },
      ]
    );
  };

  const UserCard = ({ user }) => (
    <Card style={styles.userCard}>
      <View style={styles.userHeader}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={24} color={colors.white} />
        </View>
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{user.name}</Text>
          {user.email && <Text style={styles.userDetail}>{user.email}</Text>}
          {user.phone && <Text style={styles.userDetail}>{user.phone}</Text>}
          {user.membershipType && (
            <View style={styles.membershipBadge}>
              <Text style={styles.membershipText}>{user.membershipType}</Text>
            </View>
          )}
        </View>
      </View>
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.actionButton, styles.editButton]}
          onPress={() => openModal(user)}
        >
          <Ionicons name="pencil" size={18} color={colors.primary} />
          <Text style={styles.editText}>Editar</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.deleteButton]}
          onPress={() => handleDelete(user.id, user.name)}
        >
          <Ionicons name="trash" size={18} color={colors.danger} />
          <Text style={styles.deleteText}>Eliminar</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Gestión de Usuarios</Text>
        <Text style={styles.headerSubtitle}>{users.length} miembros registrados</Text>
      </View>

      <ScrollView style={styles.content}>
        {users.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="people-outline" size={64} color={colors.gray} />
            <Text style={styles.emptyText}>No hay usuarios registrados</Text>
            <Text style={styles.emptySubtext}>
              Presiona el botón + para agregar el primer usuario
            </Text>
          </View>
        ) : (
          users.map((user) => <UserCard key={user.id} user={user} />)
        )}
      </ScrollView>

      <TouchableOpacity style={styles.fab} onPress={() => openModal()}>
        <Ionicons name="add" size={32} color={colors.white} />
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={closeModal}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
              </Text>
              <TouchableOpacity onPress={closeModal}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <Input
                label="Nombre completo *"
                value={formData.name}
                onChangeText={(text) => setFormData({ ...formData, name: text })}
                placeholder="Ej: Juan Pérez"
              />

              <Input
                label="Correo electrónico"
                value={formData.email}
                onChangeText={(text) => setFormData({ ...formData, email: text })}
                placeholder="correo@ejemplo.com"
                keyboardType="email-address"
              />

              <Input
                label="Teléfono"
                value={formData.phone}
                onChangeText={(text) => setFormData({ ...formData, phone: text })}
                placeholder="123-456-7890"
                keyboardType="phone-pad"
              />

              <Input
                label="Tipo de membresía"
                value={formData.membershipType}
                onChangeText={(text) =>
                  setFormData({ ...formData, membershipType: text })
                }
                placeholder="Ej: Mensual, Trimestral, Anual"
              />

              <Button title="Guardar" onPress={handleSave} />
              <Button
                title="Cancelar"
                onPress={closeModal}
                variant="secondary"
              />
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
    backgroundColor: colors.primary,
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
  userCard: {
    marginBottom: 12,
  },
  userHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  userInfo: {
    flex: 1,
    marginLeft: 12,
  },
  userName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  userDetail: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 2,
  },
  membershipBadge: {
    backgroundColor: colors.primary + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  membershipText: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  editButton: {
    backgroundColor: colors.primary + '10',
  },
  deleteButton: {
    backgroundColor: colors.danger + '10',
  },
  editText: {
    marginLeft: 6,
    color: colors.primary,
    fontWeight: '600',
  },
  deleteText: {
    marginLeft: 6,
    color: colors.danger,
    fontWeight: '600',
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
    backgroundColor: colors.primary,
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
    maxHeight: '90%',
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
});

export default UsersScreen;
