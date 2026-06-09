import React, { PropsWithChildren } from 'react';
import { StyleSheet, View } from 'react-native';

export function Panel({ children }: PropsWithChildren) {
  return <View style={styles.panel}>{children}</View>;
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: '#ffffff',
    borderColor: '#e2e8f0',
    borderRadius: 8,
    borderWidth: 1,
    gap: 12,
    padding: 14,
  },
});
