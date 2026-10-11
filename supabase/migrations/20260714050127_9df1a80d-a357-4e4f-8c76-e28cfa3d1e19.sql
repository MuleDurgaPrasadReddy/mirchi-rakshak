
CREATE POLICY "scan owner read" ON storage.objects FOR SELECT TO authenticated
  USING (bucket_id = 'scans' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "scan owner upload" ON storage.objects FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'scans' AND auth.uid()::text = (storage.foldername(name))[1]);
CREATE POLICY "scan owner delete" ON storage.objects FOR DELETE TO authenticated
  USING (bucket_id = 'scans' AND auth.uid()::text = (storage.foldername(name))[1]);
