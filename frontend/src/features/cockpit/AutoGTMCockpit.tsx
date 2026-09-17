"use client";

import React, { useState } from "react";
import {
  Building2,
  Users,
  Mail,
  Search,
  Check,
  CheckCircle2,
  ExternalLink,
  Send,
  Loader2,
  Linkedin,
  Shield,
  Flame,
  Zap,
} from "lucide-react";
import { useCockpit, ContactItem, TargetCompanyItem } from "./CockpitContext";
import { CampaignLaunchModal } from "./CampaignLaunchModal";

export function AutoGTMCockpit() {
  const {
    activeTab,
    setActiveTab,
    filteredContacts,
    activeContact,
    setActiveContactId,
    updateDraft,
    sendEmail,
    sendingContactId,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    filteredCompanies,
  } = useCockpit();

  const [copiedEmail, setCopiedEmail] = useState(false);

  const handleCopyEmail = (email: string) => {
    if (!email) return;
    navigator.clipboard.writeText(email);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F6F7F9] text-[#111318] overflow-hidden select-none">
      {/* Sub-Header Tabs */}
      <div className="h-12 px-6 border-b border-[#DDE2E8] bg-[#FFFFFF] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-1 p-1 bg-[#F1F3F6] border border-[#DDE2E8] rounded-lg">
          <button
            type="button"
            onClick={() => setActiveTab("companies")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "companies"
                ? "bg-[#FFFFFF] text-[#111318] font-semibold shadow-2xs border border-[#DDE2E8]"
                : "text-[#4D5663] hover:text-[#111318] hover:bg-[#E9ECF0]"
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
                ? "bg-[#FFFFFF] text-[#111318] font-semibold shadow-2xs border border-[#DDE2E8]"
                : "text-[#4D5663] hover:text-[#111318] hover:bg-[#E9ECF0]"
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
                ? "bg-[#FFFFFF] text-[#111318] font-semibold shadow-2xs border border-[#DDE2E8]"
                : "text-[#4D5663] hover:text-[#111318] hover:bg-[#E9ECF0]"
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Emails</span>
          </button>
        </div>

        {/* Global Search Bar */}
        <div className="w-72 relative">
          <Search className="w-3.5 h-3.5 text-[#818A97] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search accounts, people, or signals..."
            className="w-full bg-[#FFFFFF] border border-[#DDE2E8] rounded-md pl-8 pr-3 py-1 text-xs text-[#111318] placeholder:text-[#818A97] outline-none focus:border-[#315EF5] transition-colors"
          />
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 overflow-hidden p-6">
        {/* VIEW 1: EMAILS (Master-Detail Split Composer) */}
        {activeTab === "emails" && (
          <div className="h-full grid grid-cols-12 gap-6">
            {/* Left Contact List Sub-pane (5 cols) */}
            <div className="col-span-5 flex flex-col h-full bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl overflow-hidden shadow-2xs">
              {/* Filter controls */}
              <div className="p-3 border-b border-[#DDE2E8] bg-[#FFFFFF] flex items-center justify-between text-xs">
                <span className="font-semibold text-[#111318] text-xs">
                  Contacts ({filteredContacts.length})
                </span>
                <div className="flex items-center gap-1 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setStatusFilter("all")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "all"
                        ? "bg-[#F1F3F6] text-[#111318] font-semibold border border-[#DDE2E8]"
                        : "text-[#4D5663] hover:text-[#111318]"
                    }`}
                  >
                    All
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("verified")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "verified"
                        ? "bg-[#EAF7F1] text-[#16825D] font-semibold border border-[#BDE8D6]"
                        : "text-[#4D5663] hover:text-[#111318]"
                    }`}
                  >
                    Verified
                  </button>
                  <button
                    type="button"
                    onClick={() => setStatusFilter("missing")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "missing"
                        ? "bg-[#FFF5E5] text-[#A86514] font-semibold border border-[#F5DCB7]"
                        : "text-[#4D5663] hover:text-[#111318]"
                    }`}
                  >
                    Missing
                  </button>
                </div>
              </div>

              {/* Scrollable contact cards */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                {filteredContacts.length === 0 ? (
                  <div className="text-center py-12 text-[#818A97] text-xs">
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
                            ? "bg-[#EDF2FF] border-[#C9D5FF] shadow-2xs ring-1 ring-[#315EF5]/30"
                            : "bg-[#FFFFFF] border-[#DDE2E8] hover:bg-[#F6F7F9] hover:border-[#BFC7D1]"
                        }`}
                      >
                        {/* Header: Avatar, Name, Title, Check/Cross */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2.5 min-w-0">
                            {contact.avatarUrl ? (
                              <img
                                src={contact.avatarUrl}
                                alt={contact.name}
                                className="w-8 h-8 rounded-full object-cover border border-[#DDE2E8]"
                              />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-[#F1F3F6] border border-[#DDE2E8] flex items-center justify-center font-bold text-xs text-[#4D5663] flex-shrink-0">
                                {contact.initials}
                              </div>
                            )}

                            <div className="min-w-0">
                              <div className="text-xs font-semibold text-[#111318] truncate">
                                {contact.name}
                              </div>
                              <div className="text-[11px] text-[#4D5663] truncate">
                                {contact.title} &middot; {contact.domain}
                              </div>
                            </div>
                          </div>

                          {/* Verification Icon */}
                          <div className="flex-shrink-0 pt-0.5">
                            {hasEmail ? (
                              <div className="w-4 h-4 rounded-full border border-[#16825D] bg-[#EAF7F1] flex items-center justify-center text-[#16825D]">
                                <Check className="w-2.5 h-2.5 stroke-[2.5]" />
                              </div>
                            ) : (
                              <div className="w-4 h-4 rounded-full border border-[#DDE2E8] bg-[#F1F3F6] flex items-center justify-center text-[#818A97]">
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
                              className="px-2 py-0.5 rounded text-[10px] bg-[#F1F3F6] border border-[#DDE2E8] text-[#4D5663] flex items-center gap-1 font-mono"
                            >
                              {p.name === "hunter" && <Flame className="w-2.5 h-2.5 text-orange-500" />}
                              {p.name === "findymail" && <Zap className="w-2.5 h-2.5 text-amber-500" />}
                              {p.name === "exreacher" && <Shield className="w-2.5 h-2.5 text-[#315EF5]" />}
                              {p.name === "leadmagic" && <Mail className="w-2.5 h-2.5 text-purple-500" />}
                              <span>{p.name}</span>
                            </span>
                          ))}
                        </div>

                        {/* Direct email line */}
                        <div className="pt-2 border-t border-[#E9ECF0] flex items-center justify-between text-[11px]">
                          {hasEmail ? (
                            <div className="flex items-center gap-1.5 truncate">
                              <span className="font-mono text-[#111318] truncate font-medium">
                                {contact.email}
                              </span>
                              <span className="text-[#818A97] text-[10px]">via {contact.provider}</span>
                              {contact.emailStatus === "catch_all" && (
                                <span className="px-1.5 py-0.2 bg-[#FFF5E5] border border-[#F5DCB7] text-[#A86514] text-[9px] rounded font-mono font-medium">
                                  catch_all
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-[#818A97] italic text-[10px]">
                              no email found
                            </span>
                          )}

                          {contact.emailDraft.sent && (
                            <span className="px-1.5 py-0.5 bg-[#EAF7F1] text-[#16825D] border border-[#BDE8D6] text-[10px] rounded font-medium">
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
                  <div className="bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl p-4 flex items-center justify-between shadow-2xs">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#F1F3F6] border border-[#DDE2E8] flex items-center justify-center font-bold text-sm text-[#111318]">
                        {activeContact.initials}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-[#111318] text-sm">
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
                        <div className="text-xs text-[#4D5663]">
                          {activeContact.title} &middot; {activeContact.domain}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleCopyEmail(activeContact.email)}
                        className="px-3 py-1.5 bg-[#F6F7F9] hover:bg-[#ECEFF3] border border-[#DDE2E8] rounded-lg text-xs text-[#111318] font-medium transition-colors"
                      >
                        {copiedEmail ? "Copied!" : "Copy Email"}
                      </button>
                    </div>
                  </div>

                  {/* Email Composer Box */}
                  <div className="flex-1 bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl flex flex-col overflow-hidden shadow-2xs">
                    {/* Headers: To & Subject */}
                    <div className="p-4 border-b border-[#DDE2E8] space-y-2.5 bg-[#F6F7F9]">
                      {/* To Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-[#818A97] w-8 font-mono">To</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.to}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { to: e.target.value })
                          }
                          placeholder="recipient@domain.com"
                          className="flex-1 bg-transparent text-[#111318] font-mono text-xs outline-none border-b border-transparent focus:border-[#315EF5] py-0.5"
                        />
                      </div>

                      {/* Subj Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-[#818A97] w-8 font-mono">Subj</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.subject}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { subject: e.target.value })
                          }
                          className="flex-1 bg-transparent text-[#111318] font-semibold text-xs outline-none border-b border-transparent focus:border-[#315EF5] py-0.5"
                        />
                      </div>
                    </div>

                    {/* Email Body Area */}
                    <div className="flex-1 p-4 flex flex-col relative bg-[#FFFFFF]">
                      <textarea
                        value={activeContact.emailDraft.body}
                        onChange={(e) =>
                          updateDraft(activeContact.id, { body: e.target.value })
                        }
                        className="w-full flex-1 bg-transparent text-[#111318] text-xs leading-relaxed outline-none resize-none font-sans"
                        placeholder="Write your email here..."
                      />

                      <div className="text-[10px] text-[#818A97] text-right pt-2 select-none">
                        Click to edit
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="p-3.5 border-t border-[#DDE2E8] bg-[#F6F7F9] flex items-center justify-between">
                      {/* Left: Email validation status */}
                      <div className="text-xs text-[#4D5663] flex items-center gap-2">
                        {activeContact.emailDraft.sent ? (
                          <span className="text-[#16825D] flex items-center gap-1.5 font-medium text-xs">
                            <CheckCircle2 className="w-4 h-4 text-[#16825D]" />
                            <span>Sent at {activeContact.emailDraft.sentAt}</span>
                          </span>
                        ) : activeContact.emailStatus === "verified" ? (
                          <span className="text-[#4D5663] flex items-center gap-1.5 text-xs">
                            <Shield className="w-3.5 h-3.5 text-[#16825D]" />
                            <span className="font-medium text-[#111318]">Verified corporate inbox</span>
                          </span>
                        ) : activeContact.emailStatus === "catch_all" ? (
                          <span className="text-[#A86514] flex items-center gap-1.5 text-xs font-medium">
                            <span>⚠ Catch-all domain (Hunter verified)</span>
                          </span>
                        ) : (
                          <span className="text-[#818A97] text-xs">
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
                            className="px-4 py-2 bg-[#EAF7F1] border border-[#BDE8D6] text-[#16825D] rounded-lg text-xs font-semibold flex items-center gap-1.5"
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
                            className="bg-[#315EF5] hover:bg-[#244BD6] disabled:opacity-50 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99]"
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
                <div className="flex-1 flex items-center justify-center bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl text-[#818A97] text-xs">
                  Select a contact from the left pane to preview and send outreach.
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 2: TARGET COMPANIES */}
        {activeTab === "companies" && (
          <div className="h-full bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl overflow-hidden shadow-2xs flex flex-col">
            <div className="p-4 border-b border-[#DDE2E8] flex items-center justify-between bg-[#FFFFFF]">
              <div>
                <h3 className="text-sm font-semibold text-[#111318]">Target Accounts</h3>
                <p className="text-xs text-[#4D5663]">
                  Accounts matching active campaign criteria with verified timing signals.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 bg-[#F1F3F6] rounded border border-[#DDE2E8] text-[#4D5663] font-medium">
                {filteredCompanies.length} accounts found
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#DDE2E8] bg-[#F6F7F9] text-[#4D5663] font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Company</th>
                    <th className="py-3 px-4">Industry &amp; Location</th>
                    <th className="py-3 px-4">Employees</th>
                    <th className="py-3 px-4">ICP Fit</th>
                    <th className="py-3 px-4">Timing Signal</th>
                    <th className="py-3 px-4">Key Contact</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E9ECF0]">
                  {filteredCompanies.map((comp) => (
                    <tr key={comp.id} className="hover:bg-[#F6F7F9] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-[#111318]">
                        <div>{comp.name}</div>
                        <div className="text-[11px] text-[#818A97] font-mono">{comp.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 text-[#4D5663]">
                        <div>{comp.industry}</div>
                        <div className="text-[11px] text-[#818A97]">{comp.location}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-[#111318]">
                        {comp.employeeCount.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-[#EAF7F1] border border-[#BDE8D6] text-[#16825D] font-bold">
                          {Math.round(comp.fitScore * 100)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-[#4D5663] text-[11px] max-w-xs truncate">
                        {comp.timingSignal}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-[#111318]">{comp.keyContactName}</div>
                        <div className="text-[11px] text-[#818A97]">{comp.keyContactRole}</div>
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
                          className="px-3 py-1.5 bg-[#315EF5] hover:bg-[#244BD6] text-white font-semibold rounded-lg text-xs transition-colors"
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
          <div className="h-full bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl overflow-hidden shadow-2xs flex flex-col">
            <div className="p-4 border-b border-[#DDE2E8] flex items-center justify-between bg-[#FFFFFF]">
              <div>
                <h3 className="text-sm font-semibold text-[#111318]">Target Decision Makers</h3>
                <p className="text-xs text-[#4D5663]">
                  Verified executive buyers across target accounts with direct waterfall verification.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 bg-[#F1F3F6] rounded border border-[#DDE2E8] text-[#4D5663] font-medium">
                {filteredContacts.length} people identified
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#DDE2E8] bg-[#F6F7F9] text-[#4D5663] font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Decision Maker</th>
                    <th className="py-3 px-4">Role &amp; Company</th>
                    <th className="py-3 px-4">Verified Email</th>
                    <th className="py-3 px-4">Waterfall Providers</th>
                    <th className="py-3 px-4">Fit Score</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E9ECF0]">
                  {filteredContacts.map((person) => (
                    <tr key={person.id} className="hover:bg-[#F6F7F9] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-[#111318]">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-[#F1F3F6] border border-[#DDE2E8] flex items-center justify-center font-bold text-[11px] text-[#111318]">
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
                      <td className="py-3.5 px-4 text-[#4D5663]">
                        <div>{person.title}</div>
                        <div className="text-[11px] text-[#818A97] font-mono">{person.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        {person.email ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-[#111318] font-medium">{person.email}</span>
                            {person.emailStatus === "catch_all" && (
                              <span className="px-1.5 py-0.2 bg-[#FFF5E5] border border-[#F5DCB7] text-[#A86514] text-[9px] rounded">
                                catch_all
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-[#818A97] italic text-[11px]">no email found</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1 font-mono">
                          {person.providers.map((p) => (
                            <span
                              key={p.name}
                              className="px-1.5 py-0.5 rounded text-[10px] bg-[#F1F3F6] border border-[#DDE2E8] text-[#4D5663]"
                            >
                              {p.name}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-[#EAF7F1] border border-[#BDE8D6] text-[#16825D] font-bold">
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
                          className="px-3 py-1.5 bg-[#315EF5] hover:bg-[#244BD6] text-white font-semibold rounded-lg text-xs transition-colors"
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
