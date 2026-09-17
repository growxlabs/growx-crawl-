"use client";

import React, { createContext, useContext, useState } from "react";

export interface EvidenceDrawerData {
  isOpen: boolean;
  evidenceId?: string;
  factId?: string;
  claim?: string;
  sourceUrl?: string;
  verificationStatus?: string;
  confidenceScore?: number;
  extractedAt?: string;
  rawSnippet?: string;
  method?: string;
  observationId?: string;
  verificationRunId?: string;
  objectRef?: string;
}

interface EvidenceContextType {
  drawerData: EvidenceDrawerData;
  openEvidenceDrawer: (data: Partial<EvidenceDrawerData>) => void;
  closeEvidenceDrawer: () => void;
  correctionModalOpen: boolean;
  correctionTarget: { factId?: string; claim?: string; companyId?: string } | null;
  openCorrectionModal: (target: { factId?: string; claim?: string; companyId?: string }) => void;
  closeCorrectionModal: () => void;
}

const EvidenceContext = createContext<EvidenceContextType | undefined>(undefined);

export function EvidenceProvider({ children }: { children: React.ReactNode }) {
  const [drawerData, setDrawerData] = useState<EvidenceDrawerData>({ isOpen: false });
  const [correctionModalOpen, setCorrectionModalOpen] = useState<boolean>(false);
  const [correctionTarget, setCorrectionTarget] = useState<{ factId?: string; claim?: string; companyId?: string } | null>(null);

  const openEvidenceDrawer = (data: Partial<EvidenceDrawerData>) => {
    setDrawerData({
      isOpen: true,
      evidenceId: data.evidenceId,
      factId: data.factId,
      claim: data.claim,
      sourceUrl: data.sourceUrl,
      verificationStatus: data.verificationStatus || "Verified",
      confidenceScore: data.confidenceScore ?? 0.95,
      extractedAt: data.extractedAt || new Date().toISOString(),
      rawSnippet: data.rawSnippet,
      method: data.method || "dom_text_parser",
      observationId: data.observationId,
      verificationRunId: data.verificationRunId,
      objectRef: data.objectRef,
    });
  };

  const closeEvidenceDrawer = () => {
    setDrawerData((prev) => ({ ...prev, isOpen: false }));
  };

  const openCorrectionModal = (target: { factId?: string; claim?: string; companyId?: string }) => {
    setCorrectionTarget(target);
    setCorrectionModalOpen(true);
  };

  const closeCorrectionModal = () => {
    setCorrectionModalOpen(false);
    setCorrectionTarget(null);
  };

  return (
    <EvidenceContext.Provider
      value={{
        drawerData,
        openEvidenceDrawer,
        closeEvidenceDrawer,
        correctionModalOpen,
        correctionTarget,
        openCorrectionModal,
        closeCorrectionModal,
      }}
    >
      {children}
    </EvidenceContext.Provider>
  );
}

export function useEvidence() {
  const context = useContext(EvidenceContext);
  if (!context) {
    throw new Error("useEvidence must be used within an EvidenceProvider");
  }
  return context;
}
