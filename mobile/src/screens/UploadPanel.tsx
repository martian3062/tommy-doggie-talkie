import React, { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

import { ApiClient } from '../api/client';
import { supabase, supabaseBucket, supabaseConfigured } from '../api/supabase';
import { AnalysisJob, AnalysisResult, Dog } from '../types';
import { Panel } from '../components/Panel';
import { PrimaryButton } from '../components/PrimaryButton';

type Props = {
  api: ApiClient;
  dog: Dog;
  ownerId: string;
  onJobDone: (job: AnalysisJob, result: AnalysisResult) => void;
};

export function UploadPanel({ api, dog, ownerId, onJobDone }: Props) {
  const [context, setContext] = useState('play, toy');
  const [loading, setLoading] = useState(false);

  async function pickVideo() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Video library permission is needed to upload a clip.');
      return;
    }
    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      quality: 0.8,
      videoMaxDuration: 120,
    });
    if (picked.canceled || !picked.assets[0]) {
      return;
    }
    await submitVideo(picked.assets[0].uri);
  }

  async function recordVideo() {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Camera permission is needed to record a clip.');
      return;
    }
    const captured = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      quality: 0.8,
      videoMaxDuration: 60,
    });
    if (captured.canceled || !captured.assets[0]) {
      return;
    }
    await submitVideo(captured.assets[0].uri);
  }

  async function submitVideo(uri: string) {
    setLoading(true);
    try {
      const contextTags = context
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean);
      const fileName = `${Date.now()}.mp4`;
      let storagePath: string | undefined;
      let storageSignedUrl: string | undefined;
      let directFile:
        | {
            uri: string;
            name: string;
            type: string;
          }
        | undefined = { uri, name: fileName, type: 'video/mp4' };

      if (supabaseConfigured) {
        const response = await fetch(uri);
        const blob = await response.blob();
        storagePath = `${ownerId}/${dog.id}/${fileName}`;
        const { error } = await supabase.storage.from(supabaseBucket).upload(storagePath, blob, {
          contentType: 'video/mp4',
          upsert: false,
        });
        if (error) {
          throw error;
        }
        const signed = await supabase.storage.from(supabaseBucket).createSignedUrl(storagePath, 3600);
        if (signed.error) {
          throw signed.error;
        }
        storageSignedUrl = signed.data.signedUrl;
        directFile = undefined;
      }

      const job = await api.createAnalysisJob({
        dogId: dog.id,
        contextTags,
        file: directFile,
        storagePath,
        storageSignedUrl,
      });
      const result = await api.getResult(job.id);
      onJobDone(job, result);
    } catch (error) {
      Alert.alert('Analysis failed', error instanceof Error ? error.message : String(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Panel>
      <Text style={styles.heading}>Analyze {dog.name}</Text>
      <Text style={styles.copy}>Add context tags so the first baseline has useful clues.</Text>
      <TextInput style={styles.input} value={context} onChangeText={setContext} placeholder="play, toy, food" />
      <View style={styles.buttons}>
        <PrimaryButton label="Upload video" loading={loading} onPress={pickVideo} />
        <PrimaryButton label="Record" variant="secondary" loading={loading} onPress={recordVideo} />
      </View>
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
  input: {
    backgroundColor: '#f8fafc',
    borderColor: '#cbd5e1',
    borderRadius: 8,
    borderWidth: 1,
    fontSize: 15,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  buttons: {
    flexDirection: 'row',
    gap: 10,
  },
});
