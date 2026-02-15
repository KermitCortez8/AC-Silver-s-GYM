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
import {
  addInventoryItem,
  updateInventoryItem,
  deleteInventoryItem,
  getInventory,
} from '../data/storage';

const InventoryScreen = () => {
  const [inventory, setInventory] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    quantity: '',
    location: '',
    notes: '',
  });

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = () => {
    setInventory(getInventory());
  };

  const openModal = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        name: item.name,
        category: item.category,
        quantity: item.quantity.toString(),
        location: item.location || '',
        notes: item.notes || '',
      });
    } else {
      setEditingItem(null);
      setFormData({
        name: '',
        category: '',
        quantity: '',
        location: '',
        notes: '',
      });
    }
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setEditingItem(null);
    setFormData({
      name: '',
      category: '',
      quantity: '',
      location: '',
      notes: '',
    });
  };

  const handleSave = () => {
    if (!formData.name.trim()) {
      Alert.alert('Error', 'Por favor ingresa el nombre del artículo');
      return;
    }

    if (!formData.quantity || isNaN(formData.quantity)) {
      Alert.alert('Error', 'Por favor ingresa una cantidad válida');
      return;
    }

    const itemData = {
      ...formData,
      quantity: parseInt(formData.quantity),
    };

    if (editingItem) {
      updateInventoryItem(editingItem.id, itemData);
      Alert.alert('Éxito', 'Artículo actualizado correctamente');
    } else {
      addInventoryItem(itemData);
      Alert.alert('Éxito', 'Artículo agregado correctamente');
    }

    loadInventory();
    closeModal();
  };

  const handleDelete = (id, name) => {
    Alert.alert('Confirmar', `¿Estás seguro de eliminar ${name}?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Eliminar',
        style: 'destructive',
        onPress: () => {
          deleteInventoryItem(id);
          loadInventory();
          Alert.alert('Éxito', 'Artículo eliminado');
        },
      },
    ]);
  };

  const getStockStatus = (quantity) => {
    if (quantity === 0) {
      return { text: 'Sin Stock', color: colors.danger };
    } else if (quantity < 10) {
      return { text: 'Stock Bajo', color: colors.warning };
    } else {
      return { text: 'Stock OK', color: colors.success };
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      Maquinas: 'barbell',
      Accesorios: 'fitness',
      Limpieza: 'water',
      Oficina: 'document-text',
      Otros: 'cube',
    };
    return icons[category] || 'cube';
  };

  const InventoryCard = ({ item }) => {
    const stockStatus = getStockStatus(item.quantity);

    return (
      <Card style={styles.inventoryCard}>
        <View style={styles.itemHeader}>
          <View
            style={[styles.categoryIcon, { backgroundColor: colors.accent + '20' }]}
          >
            <Ionicons
              name={getCategoryIcon(item.category)}
              size={24}
              color={colors.accent}
            />
          </View>
          <View style={styles.itemInfo}>
            <Text style={styles.itemName}>{item.name}</Text>
            {item.category && (
              <Text style={styles.itemCategory}>{item.category}</Text>
            )}
            {item.location && (
              <View style={styles.locationContainer}>
                <Ionicons
                  name="location-outline"
                  size={12}
                  color={colors.textLight}
                />
                <Text style={styles.itemLocation}>{item.location}</Text>
              </View>
            )}
          </View>
          <View style={styles.quantityContainer}>
            <Text style={styles.quantity}>{item.quantity}</Text>
            <Text style={styles.quantityLabel}>unid.</Text>
          </View>
        </View>

        <View
          style={[styles.stockBadge, { backgroundColor: stockStatus.color + '20' }]}
        >
          <Text style={[styles.stockText, { color: stockStatus.color }]}>
            {stockStatus.text}
          </Text>
        </View>

        {item.notes && (
          <Text style={styles.itemNotes} numberOfLines={2}>
            {item.notes}
          </Text>
        )}

        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.actionButton, styles.editButton]}
            onPress={() => openModal(item)}
          >
            <Ionicons name="pencil" size={18} color={colors.primary} />
            <Text style={styles.editText}>Editar</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, styles.deleteButton]}
            onPress={() => handleDelete(item.id, item.name)}
          >
            <Ionicons name="trash" size={18} color={colors.danger} />
            <Text style={styles.deleteText}>Eliminar</Text>
          </TouchableOpacity>
        </View>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Gestión de Inventario</Text>
        <Text style={styles.headerSubtitle}>
          {inventory.length} artículos en inventario
        </Text>
      </View>

      <ScrollView style={styles.content}>
        {inventory.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="cube-outline" size={64} color={colors.gray} />
            <Text style={styles.emptyText}>No hay artículos en el inventario</Text>
            <Text style={styles.emptySubtext}>
              Presiona el botón + para agregar el primer artículo
            </Text>
          </View>
        ) : (
          inventory.map((item) => <InventoryCard key={item.id} item={item} />)
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
                {editingItem ? 'Editar Artículo' : 'Nuevo Artículo'}
              </Text>
              <TouchableOpacity onPress={closeModal}>
                <Ionicons name="close" size={28} color={colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <Input
                label="Nombre del artículo *"
                value={formData.name}
                onChangeText={(text) => setFormData({ ...formData, name: text })}
                placeholder="Ej: Mancuernas 10kg"
              />

              <Input
                label="Categoría"
                value={formData.category}
                onChangeText={(text) =>
                  setFormData({ ...formData, category: text })
                }
                placeholder="Ej: Maquinas, Accesorios, Limpieza"
              />

              <Input
                label="Cantidad *"
                value={formData.quantity}
                onChangeText={(text) =>
                  setFormData({ ...formData, quantity: text })
                }
                placeholder="0"
                keyboardType="numeric"
              />

              <Input
                label="Ubicación"
                value={formData.location}
                onChangeText={(text) =>
                  setFormData({ ...formData, location: text })
                }
                placeholder="Ej: Área de pesas"
              />

              <Input
                label="Notas"
                value={formData.notes}
                onChangeText={(text) => setFormData({ ...formData, notes: text })}
                placeholder="Observaciones adicionales"
                multiline
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
    backgroundColor: colors.accent,
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
  inventoryCard: {
    marginBottom: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  categoryIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemInfo: {
    flex: 1,
    marginLeft: 12,
  },
  itemName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
  },
  itemCategory: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: 2,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },
  itemLocation: {
    fontSize: 12,
    color: colors.textLight,
    marginLeft: 4,
  },
  quantityContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  quantity: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.text,
  },
  quantityLabel: {
    fontSize: 12,
    color: colors.textLight,
  },
  stockBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  stockText: {
    fontSize: 12,
    fontWeight: '600',
  },
  itemNotes: {
    fontSize: 14,
    color: colors.textLight,
    marginBottom: 12,
    fontStyle: 'italic',
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
    backgroundColor: colors.accent,
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

export default InventoryScreen;
