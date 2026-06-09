import React from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from 'react-native';

type Props = {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
  onPress: () => void;
};

export function PrimaryButton({ label, loading, disabled, variant = 'primary', onPress }: Props) {
  const isDisabled = disabled || loading;
  return (
    <TouchableOpacity
      style={[styles.button, variant === 'secondary' ? styles.secondary : styles.primary, isDisabled && styles.disabled]}
      onPress={onPress}
      disabled={isDisabled}
    >
      {loading ? <ActivityIndicator color={variant === 'secondary' ? '#1d4ed8' : '#ffffff'} /> : null}
      <Text style={[styles.label, variant === 'secondary' ? styles.secondaryLabel : styles.primaryLabel]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderRadius: 8,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    minHeight: 44,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  primary: {
    backgroundColor: '#2563eb',
  },
  secondary: {
    backgroundColor: '#dbeafe',
  },
  disabled: {
    opacity: 0.6,
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
  },
  primaryLabel: {
    color: '#ffffff',
  },
  secondaryLabel: {
    color: '#1d4ed8',
  },
});
