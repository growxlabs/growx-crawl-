"use client";

import React, { useState } from "react";
import {
  Building2,
  Users,
  Mail,
  Search,
  Check,
  Flame,
  Zap,
  Shield,
  Send,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { useCockpit } from "./CockpitContext";
import { CampaignLaunchModal } from "./CampaignLaunchModal";

export function AutoGTMCockpit() {
  const {
    activeTab,
    setActiveTab,
    companies,
    contacts,
    activeContactId,
    setActiveContactId,
    activeCampaignId,
    updateDraft,
    sendEmail,
    sendingContactId,
  } = useCockpit();

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "verified" | "missing">("all");
  const [copiedEmail, setCopiedEmail] = useState(false);

  // Filter contacts by active campaign, search, and status
  const filteredContacts = contacts.filter((c) => {
    if (activeCampaignId && c.campaignId !== activeCampaignId) return false;
    if (statusFilter === "verified" && c.emailStatus === "missing") return false;
    if (statusFilter === "missing" && c.emailStatus !== "missing") return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = c.name.toLowerCase().includes(q);
      const matchCompany = c.companyName.toLowerCase().includes(q);
      const matchEmail = c.email.toLowerCase().includes(q);
      const matchTitle = c.title.toLowerCase().includes(q);
      return matchName || matchCompany || matchEmail || matchTitle;
    }
    return true;
  });

  // Filter companies by search query
  const filteredCompanies = companies.filter((comp) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        comp.name.toLowerCase().includes(q) ||
        comp.domain.toLowerCase().includes(q) ||
        comp.industry.toLowerCase().includes(q) ||
        comp.keyContactName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const activeContact =
    filteredContacts.find((c) => c.id === activeContactId) || filteredContacts[0];

  const handleCopyEmail = (email: string) => {
    if (!email) return;
    navigator.clipboard.writeText(email);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-gx-canvas select-none">
      {/* Sub-Header Tabs */}
      <div className="h-12 px-6 border-b border-gx-border bg-gx-surface flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-1 p-1 bg-gx-surface-soft border border-gx-border rounded-lg">
          <button
            type="button"
            onClick={() => setActiveTab("companies")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "companies"
                ? "bg-gx-surface text-gx-ink font-semibold shadow-2xs border border-gx-border"
                : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover"
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Companies</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("people")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "people"
                ? "bg-gx-surface text-gx-ink font-semibold shadow-2xs border border-gx-border"
                : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>People</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("emails")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "emails"
                ? "bg-gx-surface text-gx-ink font-semibold shadow-2xs border border-gx-border"
                : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover"
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Emails</span>
          </button>
        </div>

        {/* Global Search Bar */}
        <div className="w-72 relative">
          <Search className="w-3.5 h-3.5 text-gx-ink-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search accounts, people, or signals..."
            className="w-full bg-gx-surface border border-gx-border rounded-md pl-8 pr-3 py-1 text-xs text-gx-ink placeholder:text-gx-ink-muted outline-none focus:border-gx-primary transition-colors"
          />
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 overflow-hidden p-6">
        {/* VIEW 1: EMAILS (Master-Detail Split Composer) */}
        {activeTab === "emails" && (
          <div className="h-full grid grid-cols-12 gap-6">
            {/* Left Contact List Sub-pane (5 cols) */}
            <div className="col-span-5 flex flex-col h-full bg-gx-surface border border-gx-border rounded-xl overflow-hidden shadow-2xs">
              {/* Filter controls */}
              <div className="p-3 border-b border-gx-border bg-gx-surface flex items-center justify-between text-xs">
                <span className="font-semibold text-gx-ink text-xs">
                  Contacts ({filteredContacts.length})
                </span>
                <div className="flex items-center gap-1 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setStatusFilter("all")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "all"
                        ? "bg-gx-surface-soft text-gx-ink font-semibold border border-gx-border"
                        : "text-gx-ink-secondary hover:text-gx-ink"
                    }`}
                  >
                    All
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("verified")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "verified"
                        ? "bg-gx-success-soft text-gx-success font-semibold border border-gx-success/30"
                        : "text-gx-ink-secondary hover:text-gx-ink"
                    }`}
                  >
                    Verified
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("missing")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "missing"
                        ? "bg-gx-warning-soft text-gx-warning font-semibold border border-gx-warning/30"
                        : "text-gx-ink-secondary hover:text-gx-ink"
                    }`}
                  >
                    Missing
                  </button>
                </div>
              </div>

              {/* Scrollable contact cards */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                {filteredContacts.length === 0 ? (
                  <div className="text-center py-12 text-gx-ink-muted text-xs">
                    No contacts match the current filter or search.
                  </div>
                ) : (
                  filteredContacts.map((contact) => {
                    const isSelected = contact.id === activeContact?.id;
                    const hasEmail = contact.emailStatus !== "missing";

                    return (
                      <div
                        key={contact.id}
                        onClick={() => setActiveContactId(contact.id)}
                        className={`p-3 rounded-xl border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-gx-primary-soft border-gx-primary-border shadow-2xs ring-1 ring-gx-primary/30"
                            : "bg-gx-surface border-gx-border hover:bg-gx-surface-hover hover:border-gx-border-strong"
                        }`}
                      >
                        {/* Header: Avatar, Name, Title, Check/Cross */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2.5 min-w-0">
                            {contact.avatarUrl ? (
                              <img
                                src={contact.avatarUrl}
                                alt={contact.name}
                                className="w-8 h-8 rounded-full object-cover border border-gx-border"
                              />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-gx-surface-soft border border-gx-border flex items-center justify-center font-bold text-xs text-gx-ink-secondary flex-shrink-0">
                                {contact.initials}
                              </div>
                            )}

                            <div className="min-w-0">
                              <div className="text-xs font-semibold text-gx-ink truncate">
                                {contact.name}
                              </div>
                              <div className="text-[11px] text-gx-ink-secondary truncate">
                                {contact.title} &middot; {contact.domain}
                              </div>
                            </div>
                          </div>

                          {/* Verification Icon */}
                          <div className="flex-shrink-0 pt-0.5">
                            {hasEmail ? (
                              <div className="w-4 h-4 rounded-full border border-gx-success bg-gx-success-soft flex items-center justify-center text-gx-success">
                                <Check className="w-2.5 h-2.5 stroke-[2.5]" />
                              </div>
                            ) : (
                              <div className="w-4 h-4 rounded-full border border-gx-border bg-gx-surface-soft flex items-center justify-center text-gx-ink-muted">
                                <span className="text-[9px] font-bold">&times;</span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Providers Pill Row */}
                        <div className="flex items-center gap-1.5 mb-2 overflow-x-auto py-0.5">
                          {contact.providers.map((p) => (
                            <span
                              key={p.name}
                              className="px-2 py-0.5 rounded text-[10px] bg-gx-surface-soft border border-gx-border text-gx-ink-secondary flex items-center gap-1 font-mono"
                            >
                              {p.name === "hunter" && <Flame className="w-2.5 h-2.5 text-orange-500" />}
                              {p.name === "findymail" && <Zap className="w-2.5 h-2.5 text-amber-500" />}
                              {p.name === "exreacher" && <Shield className="w-2.5 h-2.5 text-gx-primary" />}
                              {p.name === "leadmagic" && <Mail className="w-2.5 h-2.5 text-purple-500" />}
                              <span>{p.name}</span>
                            </span>
                          ))}
                        </div>

                        {/* Direct email line */}
                        <div className="pt-2 border-t border-gx-border-soft flex items-center justify-between text-[11px]">
                          {hasEmail ? (
                            <div className="flex items-center gap-1.5 truncate">
                              <span className="font-mono text-gx-ink truncate font-medium">
                                {contact.email}
                              </span>
                              <span className="text-gx-ink-muted text-[10px]">via {contact.provider}</span>
                              {contact.emailStatus === "catch_all" && (
                                <span className="px-1.5 py-0.2 bg-gx-warning-soft border border-gx-warning/30 text-gx-warning text-[9px] rounded font-mono font-medium">
                                  catch_all
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-gx-ink-muted italic text-[10px]">
                              no email found
                            </span>
                          )}

                          {contact.emailDraft.sent && (
                            <span className="px-1.5 py-0.5 bg-gx-success-soft text-gx-success border border-gx-success/30 text-[10px] rounded font-medium">
                              Sent
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Right Outreach Composer Sub-pane (7 cols) */}
            <div className="col-span-7 flex flex-col h-full space-y-4">
              {activeContact ? (
                <>
                  {/* Recipient Profile Header */}
                  <div className="bg-gx-surface border border-gx-border rounded-xl p-4 flex items-center justify-between shadow-2xs">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gx-surface-soft border border-gx-border flex items-center justify-center font-bold text-sm text-gx-ink">
                        {activeContact.initials}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gx-ink text-sm">
                            {activeContact.name}
                          </span>
                          <a
                            href={activeContact.linkedinUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="w-4 h-4 bg-[#0A66C2] hover:bg-[#084e96] rounded text-white flex items-center justify-center text-[10px] font-bold"
                            title="Open LinkedIn profile"
                          >
                            in
                          </a>
                        </div>
                        <div className="text-xs text-gx-ink-secondary">
                          {activeContact.title} &middot; {activeContact.domain}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleCopyEmail(activeContact.email)}
                        className="px-3 py-1.5 bg-gx-surface-soft hover:bg-gx-surface-hover border border-gx-border rounded-lg text-xs text-gx-ink font-medium transition-colors"
                      >
                        {copiedEmail ? "Copied!" : "Copy Email"}
                      </button>
                    </div>
                  </div>

                  {/* Email Composer Box */}
                  <div className="flex-1 bg-gx-surface border border-gx-border rounded-xl flex flex-col overflow-hidden shadow-2xs">
                    {/* Headers: To & Subject */}
                    <div className="p-4 border-b border-gx-border space-y-2.5 bg-gx-surface-soft">
                      {/* To Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gx-ink-muted w-8 font-mono">To</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.to}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { to: e.target.value })
                          }
                          placeholder="recipient@domain.com"
                          className="flex-1 bg-transparent text-gx-ink font-mono text-xs outline-none border-b border-transparent focus:border-gx-primary py-0.5"
                        />
                      </div>

                      {/* Subj Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gx-ink-muted w-8 font-mono">Subj</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.subject}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { subject: e.target.value })
                          }
                          className="flex-1 bg-transparent text-gx-ink font-semibold text-xs outline-none border-b border-transparent focus:border-gx-primary py-0.5"
                        />
                      </div>
                    </div>

                    {/* Email Body Area */}
                    <div className="flex-1 p-4 flex flex-col relative bg-gx-surface">
                      <textarea
                        value={activeContact.emailDraft.body}
                        onChange={(e) =>
                          updateDraft(activeContact.id, { body: e.target.value })
                        }
                        className="w-full flex-1 bg-transparent text-gx-ink text-xs leading-relaxed outline-none resize-none font-sans"
                        placeholder="Write your email here..."
                      />

                      <div className="text-[10px] text-gx-ink-muted text-right pt-2 select-none">
                        Click to edit
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="p-3.5 border-t border-gx-border bg-gx-surface-soft flex items-center justify-between">
                      {/* Left: Email validation status */}
                      <div className="text-xs text-gx-ink-secondary flex items-center gap-2">
                        {activeContact.emailDraft.sent ? (
                          <span className="text-gx-success flex items-center gap-1.5 font-medium text-xs">
                            <CheckCircle2 className="w-4 h-4 text-gx-success" />
                            <span>Sent at {activeContact.emailDraft.sentAt}</span>
                          </span>
                        ) : activeContact.emailStatus === "verified" ? (
                          <span className="text-gx-ink-secondary flex items-center gap-1.5 text-xs">
                            <Shield className="w-3.5 h-3.5 text-gx-success" />
                            <span className="font-medium text-gx-ink">Verified corporate inbox</span>
                          </span>
                        ) : activeContact.emailStatus === "catch_all" ? (
                          <span className="text-gx-warning flex items-center gap-1.5 text-xs font-medium">
                            <span>⚠ Catch-all domain (Hunter verified)</span>
                          </span>
                        ) : (
                          <span className="text-gx-ink-muted text-xs">
                            No verified email found for this profile
                          </span>
                        )}
                      </div>

                      {/* Right: Send CTA */}
                      <div>
                        {activeContact.emailDraft.sent ? (
                          <button
                            type="button"
                            disabled
                            className="px-4 py-2 bg-gx-success-soft border border-gx-success/30 text-gx-success rounded-lg text-xs font-semibold flex items-center gap-1.5"
                          >
                            <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                            <span>Sent to {activeContact.emailDraft.to}</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            onClick={() => sendEmail(activeContact.id)}
                            disabled={
                              sendingContactId === activeContact.id ||
                              !activeContact.emailDraft.to
                            }
                            className="bg-gx-primary hover:bg-gx-primary-hover disabled:opacity-50 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99]"
                          >
                            {sendingContactId === activeContact.id ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span>Sending...</span>
                              </>
                            ) : (
                              <>
                                <Send className="w-3.5 h-3.5" />
                                <span>Claim $30 credits &amp; send</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center bg-gx-surface border border-gx-border rounded-xl text-gx-ink-muted text-xs">
                  Select a contact from the left pane to preview and send outreach.
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 2: TARGET COMPANIES */}
        {activeTab === "companies" && (
          <div className="h-full bg-gx-surface border border-gx-border rounded-xl overflow-hidden shadow-2xs flex flex-col">
            <div className="p-4 border-b border-gx-border flex items-center justify-between bg-gx-surface">
              <div>
                <h3 className="text-sm font-semibold text-gx-ink">Target Accounts</h3>
                <p className="text-xs text-gx-ink-secondary">
                  Accounts matching active campaign criteria with verified timing signals.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 bg-gx-surface-soft rounded border border-gx-border text-gx-ink-secondary font-medium">
                {filteredCompanies.length} accounts found
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-gx-border bg-gx-surface-soft text-gx-ink-secondary font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Company</th>
                    <th className="py-3 px-4">Industry &amp; Location</th>
                    <th className="py-3 px-4">Employees</th>
                    <th className="py-3 px-4">ICP Fit</th>
                    <th className="py-3 px-4">Timing Signal</th>
                    <th className="py-3 px-4">Key Contact</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gx-border-soft">
                  {filteredCompanies.map((comp) => (
                    <tr key={comp.id} className="hover:bg-gx-surface-hover transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-gx-ink">
                        <div>{comp.name}</div>
                        <div className="text-[11px] text-gx-ink-muted font-mono">{comp.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 text-gx-ink-secondary">
                        <div>{comp.industry}</div>
                        <div className="text-[11px] text-gx-ink-muted">{comp.location}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-gx-ink">
                        {comp.employeeCount.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-gx-success-soft border border-gx-success/30 text-gx-success font-bold">
                          {Math.round(comp.fitScore * 100)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-gx-ink-secondary text-[11px] max-w-xs truncate">
                        {comp.timingSignal}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-gx-ink">{comp.keyContactName}</div>
                        <div className="text-[11px] text-gx-ink-muted">{comp.keyContactRole}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            const contact = filteredContacts.find(
                              (c) => c.domain === comp.domain || c.companyName === comp.name
                            );
                            if (contact) {
                              setActiveContactId(contact.id);
                            }
                            setActiveTab("emails");
                          }}
                          className="px-3 py-1.5 bg-gx-primary hover:bg-gx-primary-hover text-white font-semibold rounded-lg text-xs transition-colors"
                        >
                          Draft Email
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* VIEW 3: PEOPLE / DECISION MAKERS */}
        {activeTab === "people" && (
          <div className="h-full bg-gx-surface border border-gx-border rounded-xl overflow-hidden shadow-2xs flex flex-col">
            <div className="p-4 border-b border-gx-border flex items-center justify-between bg-gx-surface">
              <div>
                <h3 className="text-sm font-semibold text-gx-ink">Target Decision Makers</h3>
                <p className="text-xs text-gx-ink-secondary">
                  Verified executive buyers across target accounts with direct waterfall verification.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 bg-gx-surface-soft rounded border border-gx-border text-gx-ink-secondary font-medium">
                {filteredContacts.length} people identified
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-gx-border bg-gx-surface-soft text-gx-ink-secondary font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Decision Maker</th>
                    <th className="py-3 px-4">Role &amp; Company</th>
                    <th className="py-3 px-4">Verified Email</th>
                    <th className="py-3 px-4">Waterfall Providers</th>
                    <th className="py-3 px-4">Fit Score</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gx-border-soft">
                  {filteredContacts.map((person) => (
                    <tr key={person.id} className="hover:bg-gx-surface-hover transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-gx-ink">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-gx-surface-soft border border-gx-border flex items-center justify-center font-bold text-[11px] text-gx-ink">
                            {person.initials}
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span>{person.name}</span>
                              <a
                                href={person.linkedinUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="w-3.5 h-3.5 bg-[#0A66C2] rounded text-white flex items-center justify-center text-[9px] font-bold"
                              >
                                in
                              </a>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-gx-ink-secondary">
                        <div>{person.title}</div>
                        <div className="text-[11px] text-gx-ink-muted font-mono">{person.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        {person.email ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-gx-ink font-medium">{person.email}</span>
                            {person.emailStatus === "catch_all" && (
                              <span className="px-1.5 py-0.2 bg-gx-warning-soft border border-gx-warning/30 text-gx-warning text-[9px] rounded">
                                catch_all
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-gx-ink-muted italic text-[11px]">no email found</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1 font-mono">
                          {person.providers.map((p) => (
                            <span
                              key={p.name}
                              className="px-1.5 py-0.5 rounded text-[10px] bg-gx-surface-soft border border-gx-border text-gx-ink-secondary"
                            >
                              {p.name}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-gx-success-soft border border-gx-success/30 text-gx-success font-bold">
                          {Math.round(person.fitScore * 100)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => {
                            setActiveContactId(person.id);
                            setActiveTab("emails");
                          }}
                          className="px-3 py-1.5 bg-gx-primary hover:bg-gx-primary-hover text-white font-semibold rounded-lg text-xs transition-colors"
                        >
                          Compose Email
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Global Campaign Launch Modal */}
      <CampaignLaunchModal />
    </div>
  );
}
