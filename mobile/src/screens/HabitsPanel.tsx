import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { HabitSummary } from '../types';
import { Panel } from '../components/Panel';

type Props = {
  habits: HabitSummary | null;
};

export function HabitsPanel({ habits }: Props) {
  return (
    <Panel>
      <Text style={styles.heading}>Personal learning</Text>
      {!habits || Object.keys(habits.label_counts).length === 0 ? (
        <Text style={styles.copy}>Feedback will appear here as the app learns this dog's usual patterns.</Text>
      ) : (
        <View style={styles.list}>
          {Object.entries(habits.label_counts).map(([label, count]) => (
            <View key={label} style={styles.row}>
              <Text style={styles.label}>{label}</Text>
              <Text style={styles.count}>{count}</Text>
            </View>
          ))}
        </View>
      )}
      {habits?.recent_notes?.map((note) => (
        <Text key={note} style={styles.note}>
          {note}
        </Text>
      ))}
    </Panel>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  copy: {
    color: '#64748b',
    fontSize: 14,
  },
  list: {
    gap: 8,
  },
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  label: {
    color: '#111827',
    fontSize: 15,
    textTransform: 'capitalize',
  },
  count: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  note: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    color: '#475569',
    padding: 10,
  },
});
