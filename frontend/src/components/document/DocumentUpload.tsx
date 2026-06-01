import {
  ActionIcon,
  Button,
  Loader,
  Text,
} from "@mantine/core";
import { IconFileUpload, IconTrash } from "@tabler/icons-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { api, type PlanDocument } from "../../api/client";
import styles from "./DocumentUpload.module.css";

const MAX_SIZE = 10 * 1024 * 1024;
const MAX_DOCS = 20;
const ALLOWED_TYPES = [".pdf", ".txt", ".md"];

interface Props {
  planId: number;
}

interface UploadControlsProps {
  fileInputRef: React.RefObject<HTMLInputElement>;
  canUpload: boolean;
  isPending: boolean;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  label: string;
}

function UploadControls({
  fileInputRef,
  canUpload,
  isPending,
  onFileChange,
  label,
}: UploadControlsProps) {
  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md"
        className={styles.fileInput}
        onChange={onFileChange}
      />
      <Button
        color="cyan"
        size="xs"
        variant="light"
        disabled={!canUpload || isPending}
        leftSection={isPending ? undefined : <IconFileUpload size={14} />}
        loading={isPending}
        onClick={() => fileInputRef.current?.click()}
      >
        {label}
      </Button>
    </>
  );
}

export default function DocumentUpload({ planId }: Props) {
  const qc = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);

  const { data: documents = [], isLoading } = useQuery<PlanDocument[]>({
    queryKey: ["documents", planId],
    queryFn: () => api.getDocuments(planId),
    enabled: !!planId,
  });

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadDocument(planId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", planId] });
    },
  });

  const remove = useMutation({
    mutationFn: (documentId: number) => api.deleteDocument(planId, documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", planId] });
    },
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_SIZE) {
      alert(`File is too large. Maximum size is 10 MB.`);
      return;
    }
    if (!ALLOWED_TYPES.some((ext) => file.name.toLowerCase().endsWith(ext))) {
      alert("Only PDF, TXT, and MD files are supported.");
      return;
    }
    upload.mutate(file);
    if (fileInput.current) fileInput.current.value = "";
  }

  const canUpload = documents.length < MAX_DOCS;

  return (
    <div>
      {isLoading ? (
        <div className={styles.loader}>
          <Loader color="cyan" size="sm" />
        </div>
      ) : documents.length === 0 ? (
        <div className={styles.empty}>
          <IconFileUpload size={28} stroke={1.2} color="var(--c-cool-gray)" />
          <Text className={styles.emptyText}>
            Upload PDF, TXT, or MD files to ask questions about your study
            materials.
          </Text>
          <UploadControls
            fileInputRef={fileInput}
            canUpload={canUpload}
            isPending={upload.isPending}
            onFileChange={handleFileChange}
            label="Upload document"
          />
        </div>
      ) : (
        <>
          <div className={styles.docList}>
            {documents.map((doc) => (
              <div key={doc.id} className={styles.docRow}>
                <div className={styles.docInfo}>
                  <Text className={styles.docName}>{doc.filename}</Text>
                  <Text className={styles.docMeta}>
                    {doc.file_type.toUpperCase()}
                  </Text>
                </div>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        size="sm"
                        loading={remove.isPending}
                        disabled={remove.isPending}
                        onClick={() => remove.mutate(doc.id)}
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </div>
            ))}
          </div>
          <div className={styles.uploadRow}>
            <UploadControls
              fileInputRef={fileInput}
              canUpload={canUpload}
              isPending={upload.isPending}
              onFileChange={handleFileChange}
              label={
                canUpload
                  ? `Upload (${documents.length}/${MAX_DOCS})`
                  : `Limit reached (${MAX_DOCS})`
              }
            />
          </div>
        </>
      )}
      {upload.isError && (
        <Text className={styles.error}>
          {upload.error instanceof Error ? upload.error.message : "Upload failed"}
        </Text>
      )}
      {remove.isError && (
        <Text className={styles.error}>
          {remove.error instanceof Error ? remove.error.message : "Delete failed"}
        </Text>
      )}
    </div>
  );
}
