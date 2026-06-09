import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity } from 'react-native';

import { Dog } from '../types';
import { Panel } from '../components/Panel';

type Props = {
  dogs: Dog[];
  selectedDogId?: string;
  onSelect: (dog: Dog) => void;
};

export function DogList({ dogs, selectedDogId, onSelect }: Props) {
  if (!dogs.length) {
    return null;
  }
  return (
    <Panel>
      <Text style={styles.heading}>Profiles</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.list}>
        {dogs.map((dog) => (
          <TouchableOpacity
            key={dog.id}
            style={[styles.chip, dog.id === selectedDogId && styles.activeChip]}
            onPress={() => onSelect(dog)}
          >
            <Text style={[styles.chipText, dog.id === selectedDogId && styles.activeText]}>{dog.name}</Text>
            {dog.breed ? <Text style={styles.breed}>{dog.breed}</Text> : null}
          </TouchableOpacity>
        ))}
      </ScrollView>
    </Panel>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  list: {
    gap: 10,
  },
  chip: {
    backgroundColor: '#f8fafc',
    borderColor: '#cbd5e1',
    borderRadius: 8,
    borderWidth: 1,
    minWidth: 110,
    padding: 12,
  },
  activeChip: {
    backgroundColor: '#dbeafe',
    borderColor: '#2563eb',
  },
  chipText: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '800',
  },
  activeText: {
    color: '#1d4ed8',
  },
  breed: {
    color: '#64748b',
    fontSize: 13,
    marginTop: 2,
  },
});
