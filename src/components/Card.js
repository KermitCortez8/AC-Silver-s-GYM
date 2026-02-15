import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import colors from '../constants/colors';

const Card = ({ children, style, title, onPress, icon }) => {
  const Container = onPress ? TouchableOpacity : View;
  
  return (
    <Container 
      style={[styles.card, style]} 
      onPress={onPress}
      activeOpacity={0.7}
    >
      {title && (
        <View style={styles.header}>
          {icon && <Ionicons name={icon} size={24} color={colors.primary} style={styles.icon} />}
          <Text style={styles.title}>{title}</Text>
        </View>
      )}
      {children}
    </Container>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.white,
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  icon: {
    marginRight: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
});

export default Card;
