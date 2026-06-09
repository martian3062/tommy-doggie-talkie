import React, { useState } from 'react';
import { Alert, SafeAreaView, StyleSheet, Text, TextInput, View } from 'react-native';

import { supabase } from '../api/supabase';
import { Panel } from '../components/Panel';
import { PrimaryButton } from '../components/PrimaryButton';

type Props = {
  onUseLocal: () => void;
};

export function AuthScreen({ onUseLocal }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function signIn() {
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      Alert.alert('Sign in failed', error.message);
    }
  }

  async function signUp() {
    setLoading(true);
    const { error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      Alert.alert('Sign up failed', error.message);
    } else {
      Alert.alert('Check email', 'Confirm the email if your Supabase project requires it.');
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.title}>Dog Translator</Text>
        <Text style={styles.subtitle}>Sign in with Supabase or continue locally while credentials are pending.</Text>
        <Panel>
          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="Email"
            style={styles.input}
            value={email}
            onChangeText={setEmail}
          />
          <TextInput
            placeholder="Password"
            secureTextEntry
            style={styles.input}
            value={password}
            onChangeText={setPassword}
          />
          <PrimaryButton label="Sign in" loading={loading} onPress={signIn} />
          <PrimaryButton label="Create account" variant="secondary" loading={loading} onPress={signUp} />
          <PrimaryButton label="Use local demo" variant="secondary" onPress={onUseLocal} />
        </Panel>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  container: {
    gap: 16,
    padding: 20,
  },
  title: {
    color: '#111827',
    fontSize: 32,
    fontWeight: '800',
  },
  subtitle: {
    color: '#475569',
    fontSize: 15,
    lineHeight: 21,
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
});
