import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

import { ApiClient } from '../api/client';
import { BreedDetection, Dog } from '../types';
import { Panel } from '../components/Panel';
import { PrimaryButton } from '../components/PrimaryButton';

type Props = {
  api: ApiClient;
  dog: Dog;
  onDogUpdated: (dog: Dog) => void;
};

export function BreedPanel({ api, dog, onDogUpdated }: Props) {
  const [loading, setLoading] = useState(false);
  const [detection, setDetection] = useState<BreedDetection | null>(null);
  const profile = detection?.behavior_profile ?? dog.breed_behavior_profile;
  const predictions = detection?.breed_predictions ?? dog.breed_predictions ?? [];

  async function chooseBreedImage() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Choose a clear dog photo or short clip to detect breed.');
      return;
    }
    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.All,
      quality: 0.9,
      videoMaxDuration: 20,
    });
    if (picked.canceled || !picked.assets[0]) {
      return;
    }
    setLoading(true);
    try {
      const asset = picked.assets[0];
      const name = asset.uri.split('/').pop() || 'breed-upload.jpg';
      const type = asset.type === 'video' ? 'video/mp4' : 'image/jpeg';
      const result = await api.detectBreed(dog.id, { uri: asset.uri, name, type });
      setDetection(result);
      const top = result.breed_predictions[0];
      onDogUpdated({
        ...dog,
        breed: result.selected_breed ?? top?.breed ?? dog.breed,
        breed_source: result.breed_source,
        breed_confidence: top?.confidence,
        breed_predictions: result.breed_predictions,
        breed_behavior_profile: result.behavior_profile ?? dog.breed_behavior_profile,
      });
    } catch (error) {
      Alert.alert('Breed detection failed', error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Panel>
      <View style={styles.header}>
        <View>
          <Text style={styles.heading}>Breed intelligence</Text>
          <Text style={styles.copy}>{dog.breed || 'Unknown breed'} · {dog.breed_source || 'manual/unknown'}</Text>
        </View>
        {dog.breed_confidence ? <Text style={styles.confidence}>{Math.round(dog.breed_confidence * 100)}%</Text> : null}
      </View>

      {profile ? (
        <View style={styles.profile}>
          <Text style={styles.profileTitle}>{profile.display_name}</Text>
          <Text style={styles.copy}>Group: {profile.group} · Energy: {profile.energy_level}</Text>
          <Text style={styles.subhead}>Common patterns</Text>
          {profile.common_patterns.map((item) => (
            <Text key={item} style={styles.item}>{item}</Text>
          ))}
          <Text style={styles.subhead}>Health watch</Text>
          {profile.health_watch.map((item) => (
            <Text key={item} style={styles.item}>{item}</Text>
          ))}
        </View>
      ) : null}

      {predictions.length ? (
        <View style={styles.predictions}>
          {predictions.slice(0, 3).map((prediction) => (
            <TouchableOpacity key={`${prediction.breed}-${prediction.confidence}`} style={styles.prediction}>
              <Text style={styles.predictionBreed}>{prediction.breed}</Text>
              <Text style={styles.copy}>{Math.round(prediction.confidence * 100)}% · {prediction.source}</Text>
            </TouchableOpacity>
          ))}
        </View>
      ) : null}

      <PrimaryButton label="Detect breed from photo" loading={loading} onPress={chooseBreedImage} />
    </Panel>
  );
}

const styles = StyleSheet.create({
  header: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  heading: {
    color: '#111827',
    fontSize: 18,
    fontWeight: '800',
  },
  copy: {
    color: '#64748b',
    fontSize: 13,
    lineHeight: 18,
  },
  confidence: {
    color: '#1d4ed8',
    fontWeight: '800',
  },
  profile: {
    gap: 6,
  },
  profileTitle: {
    color: '#111827',
    fontSize: 16,
    fontWeight: '800',
  },
  subhead: {
    color: '#334155',
    fontSize: 14,
    fontWeight: '800',
    marginTop: 4,
  },
  item: {
    color: '#475569',
    fontSize: 13,
  },
  predictions: {
    gap: 8,
  },
  prediction: {
    backgroundColor: '#f8fafc',
    borderColor: '#e2e8f0',
    borderRadius: 8,
    borderWidth: 1,
    padding: 10,
  },
  predictionBreed: {
    color: '#111827',
    fontSize: 14,
    fontWeight: '800',
  },
});
