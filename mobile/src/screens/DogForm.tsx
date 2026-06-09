import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';

import { DogPayload } from '../types';
import { Panel } from '../components/Panel';
import { PrimaryButton } from '../components/PrimaryButton';

type Props = {
  onCreate: (payload: DogPayload) => Promise<void>;
};

export function DogForm({ onCreate }: Props) {
  const [name, setName] = useState('');
  const [breed, setBreed] = useState('');
  const [routine, setRoutine] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!name.trim()) {
      Alert.alert('Name needed', 'Add your dog name first.');
      return;
    }
    setLoading(true);
    try {
      await onCreate({
        name: name.trim(),
        breed: breed.trim() || undefined,
        breed_source: breed.trim() ? 'user_selected' : 'unknown',
        routines: routine.trim() ? { notes: routine.trim() } : {},
      });
      setName('');
      setBreed('');
      setRoutine('');
    } catch (error) {
      Alert.alert('Could not create dog', error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Panel>
      <Text style={styles.heading}>Dog profile</Text>
      <View style={styles.row}>
        <TextInput placeholder="Name" style={styles.input} value={name} onChangeText={setName} />
        <TextInput placeholder="Breed" style={styles.input} value={breed} onChangeText={setBreed} />
      </View>
      <TextInput
        placeholder="Usual routine or habits"
        style={styles.input}
        value={routine}
        onChangeText={setRoutine}
      />
      <PrimaryButton label="Add dog" loading={loading} onPress={submit} />
    </Panel>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  row: {
    flexDirection: 'row',
    gap: 10,
  },
  input: {
    backgroundColor: '#f8fafc',
    borderColor: '#cbd5e1',
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
});
