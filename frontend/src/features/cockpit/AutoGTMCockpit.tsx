"use client";

import React, { useState } from "react";
import {
  Building2,
  Users,
  Mail,
  Search,
  Check,
  CheckCircle2,
  XCircle,
  ExternalLink,
  Send,
  Loader2,
  Linkedin,
  Shield,
  Sparkles,
  Flame,
  Zap,
} from "lucide-react";
import { useCockpit, ContactItem, TargetCompanyItem } from "./CockpitContext";
import { CompetitorModal } from "./CompetitorModal";
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
    <div className="flex-1 flex flex-col h-full bg-[#0a0c10] text-slate-200 overflow-hidden select-none">
      {/* Sub-Header Tabs */}
      <div className="h-12 px-6 border-b border-[#1b202c] bg-[#0d0f15] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-1.5 p-1 bg-[#141822] border border-[#202736] rounded-lg">
          <button
            onClick={() => setActiveTab("companies")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "companies"
                ? "bg-[#252d3e] text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Companies</span>
          </button>

          <button
            onClick={() => setActiveTab("people")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "people"
                ? "bg-[#252d3e] text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>People</span>
          </button>

          <button
            onClick={() => setActiveTab("emails")}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              activeTab === "emails"
                ? "bg-white text-slate-950 font-bold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Emails</span>
          </button>
        </div>

        {/* Global Search Bar */}
        <div className="w-72 relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search accounts, people, or signals..."
            className="w-full bg-[#141822] border border-[#212737] rounded-md pl-8 pr-3 py-1 text-xs text-white placeholder:text-slate-500 outline-none focus:border-slate-500 transition-colors"
          />
        </div>
      </div>

      {/* Main Workspace Area */}
      <div className="flex-1 overflow-hidden p-6">
        {/* VIEW 1: EMAILS (Core Explee Master-Detail Split Composer) */}
        {activeTab === "emails" && (
          <div className="h-full grid grid-cols-12 gap-6">
            {/* Left Contact List Sub-pane (5 cols) */}
            <div className="col-span-5 flex flex-col h-full bg-[#0e1118] border border-[#1e2434] rounded-xl overflow-hidden shadow-xl">
              {/* Filter controls */}
              <div className="p-3 border-b border-[#1b2130] flex items-center justify-between text-xs">
                <span className="font-semibold text-white text-xs">
                  Contacts ({filteredContacts.length})
                </span>
                <div className="flex items-center gap-1 text-[11px]">
                  <button
                    onClick={() => setStatusFilter("all")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "all"
                        ? "bg-[#202738] text-white font-medium"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    All
                  </button>
                  <button
                    onClick={() => setStatusFilter("verified")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "verified"
                        ? "bg-[#202738] text-emerald-400 font-medium"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Verified
                  </button>
                  <button
                    onClick={() => setStatusFilter("missing")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      statusFilter === "missing"
                        ? "bg-[#202738] text-amber-400 font-medium"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    Missing
                  </button>
                </div>
              </div>

              {/* Scrollable contact cards */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
                {filteredContacts.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-xs">
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
                            ? "bg-[#161c28] border-slate-500 shadow-lg ring-1 ring-slate-500/50"
                            : "bg-[#121620] border-[#202636] hover:bg-[#151a25] hover:border-slate-700"
                        }`}
                      >
                        {/* Header: Avatar, Name, Title, Check/Cross */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2.5 min-w-0">
                            {contact.avatarUrl ? (
                              <img
                                src={contact.avatarUrl}
                                alt={contact.name}
                                className="w-8 h-8 rounded-full object-cover border border-[#2b3348]"
                              />
                            ) : (
                              <div className="w-8 h-8 rounded-full bg-[#202738] border border-[#2c354c] flex items-center justify-center font-bold text-xs text-white flex-shrink-0">
                                {contact.initials}
                              </div>
                            )}

                            <div className="min-w-0">
                              <div className="text-xs font-bold text-white truncate">
                                {contact.name}
                              </div>
                              <div className="text-[11px] text-slate-400 truncate">
                                {contact.title} &middot; {contact.domain}
                              </div>
                            </div>
                          </div>

                          {/* Verification Icon */}
                          <div className="flex-shrink-0 pt-0.5">
                            {hasEmail ? (
                              <div className="w-4 h-4 rounded-full border border-slate-500 flex items-center justify-center text-slate-300">
                                <Check className="w-2.5 h-2.5" />
                              </div>
                            ) : (
                              <div className="w-4 h-4 rounded-full border border-slate-600 flex items-center justify-center text-slate-500">
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
                              className="px-2 py-0.5 rounded text-[10px] bg-[#181e2b] border border-[#242c3d] text-slate-400 flex items-center gap-1"
                            >
                              {p.name === "hunter" && <Flame className="w-2.5 h-2.5 text-orange-400" />}
                              {p.name === "findymail" && <Zap className="w-2.5 h-2.5 text-amber-400" />}
                              {p.name === "exreacher" && <Shield className="w-2.5 h-2.5 text-blue-400" />}
                              {p.name === "leadmagic" && <Mail className="w-2.5 h-2.5 text-purple-400" />}
                              <span>{p.name}</span>
                            </span>
                          ))}
                        </div>

                        {/* Direct email line */}
                        <div className="pt-2 border-t border-[#1b2230] flex items-center justify-between text-[11px]">
                          {hasEmail ? (
                            <div className="flex items-center gap-1.5 truncate">
                              <span className="font-mono text-slate-300 truncate">
                                {contact.email}
                              </span>
                              <span className="text-slate-500 text-[10px]">via {contact.provider}</span>
                              {contact.emailStatus === "catch_all" && (
                                <span className="px-1.5 py-0.2 bg-amber-950/80 border border-amber-600/40 text-amber-400 text-[9px] rounded font-mono">
                                  catch_all
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-500 italic text-[10px]">
                              no email found
                            </span>
                          )}

                          {contact.emailDraft.sent && (
                            <span className="px-1.5 py-0.5 bg-emerald-950/80 text-emerald-400 text-[10px] rounded font-medium">
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
                  <div className="bg-[#0e1118] border border-[#1e2434] rounded-xl p-4 flex items-center justify-between shadow-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-[#1b2232] border border-[#2b354d] flex items-center justify-center font-bold text-sm text-white">
                        {activeContact.initials}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">
                            {activeContact.name}
                          </span>
                          <a
                            href={activeContact.linkedinUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="w-4 h-4 bg-blue-600 hover:bg-blue-500 rounded text-white flex items-center justify-center text-[10px] font-bold"
                            title="Open LinkedIn profile"
                          >
                            in
                          </a>
                        </div>
                        <div className="text-xs text-slate-400">
                          {activeContact.title} &middot; {activeContact.domain}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleCopyEmail(activeContact.email)}
                        className="px-3 py-1.5 bg-[#171c28] hover:bg-[#202738] border border-[#232b3b] rounded-lg text-xs text-slate-300 hover:text-white transition-colors"
                      >
                        {copiedEmail ? "Copied!" : "Copy Email"}
                      </button>
                    </div>
                  </div>

                  {/* Email Composer Box */}
                  <div className="flex-1 bg-[#0e1118] border border-[#1e2434] rounded-xl flex flex-col overflow-hidden shadow-xl">
                    {/* Headers: To & Subject */}
                    <div className="p-4 border-b border-[#1b2130] space-y-2.5 bg-[#10141f]">
                      {/* To Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-slate-500 w-8 font-mono">To</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.to}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { to: e.target.value })
                          }
                          placeholder="recipient@domain.com"
                          className="flex-1 bg-transparent text-white font-mono text-xs outline-none border-b border-transparent focus:border-slate-600 py-0.5"
                        />
                      </div>

                      {/* Subj Field */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-slate-500 w-8 font-mono">Subj</span>
                        <input
                          type="text"
                          value={activeContact.emailDraft.subject}
                          onChange={(e) =>
                            updateDraft(activeContact.id, { subject: e.target.value })
                          }
                          className="flex-1 bg-transparent text-white font-semibold text-xs outline-none border-b border-transparent focus:border-slate-600 py-0.5"
                        />
                      </div>
                    </div>

                    {/* Email Body Area */}
                    <div className="flex-1 p-4 flex flex-col relative bg-[#0c0e14]">
                      <textarea
                        value={activeContact.emailDraft.body}
                        onChange={(e) =>
                          updateDraft(activeContact.id, { body: e.target.value })
                        }
                        className="w-full flex-1 bg-transparent text-slate-200 text-xs leading-relaxed outline-none resize-none font-sans"
                        placeholder="Write your email here..."
                      />

                      <div className="text-[10px] text-slate-500 text-right pt-2 select-none">
                        Click to edit
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="p-3.5 border-t border-[#1b2130] bg-[#10141f] flex items-center justify-between">
                      {/* Left: Email validation status */}
                      <div className="text-xs text-slate-400 flex items-center gap-2">
                        {activeContact.emailDraft.sent ? (
                          <span className="text-emerald-400 flex items-center gap-1.5 font-medium text-xs">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>Sent at {activeContact.emailDraft.sentAt}</span>
                          </span>
                        ) : activeContact.emailStatus === "verified" ? (
                          <span className="text-slate-300 flex items-center gap-1.5 text-xs">
                            <Shield className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Verified corporate inbox</span>
                          </span>
                        ) : activeContact.emailStatus === "catch_all" ? (
                          <span className="text-amber-400 flex items-center gap-1.5 text-xs">
                            <span>⚠ Catch-all domain (Hunter verified)</span>
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">
                            No verified email found for this profile
                          </span>
                        )}
                      </div>

                      {/* Right: Send CTA */}
                      <div>
                        {activeContact.emailDraft.sent ? (
                          <button
                            disabled
                            className="px-4 py-2 bg-[#192420] border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-semibold flex items-center gap-1.5"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Sent to {activeContact.emailDraft.to}</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => sendEmail(activeContact.id)}
                            disabled={
                              sendingContactId === activeContact.id ||
                              !activeContact.emailDraft.to
                            }
                            className="bg-[#00c288] hover:bg-[#00d696] disabled:opacity-50 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-2 shadow-lg shadow-emerald-950/40 transition-all hover:scale-[1.01] active:scale-[0.99]"
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
                <div className="flex-1 flex items-center justify-center bg-[#0e1118] border border-[#1e2434] rounded-xl text-slate-500 text-xs">
                  Select a contact from the left pane to preview and send outreach.
                </div>
              )}
            </div>
          </div>
        )}

        {/* VIEW 2: TARGET COMPANIES */}
        {activeTab === "companies" && (
          <div className="h-full bg-[#0e1118] border border-[#1e2434] rounded-xl overflow-hidden shadow-xl flex flex-col">
            <div className="p-4 border-b border-[#1b2130] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Target Accounts</h3>
                <p className="text-xs text-slate-400">
                  Accounts matching active campaign criteria with verified timing signals.
                </p>
              </div>
              <span className="text-xs font-mono px-2 py-1 bg-[#171c28] rounded border border-[#232a3c] text-slate-300">
                {filteredCompanies.length} accounts found
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#1b2130] bg-[#10141f] text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Company</th>
                    <th className="py-3 px-4">Industry &amp; Location</th>
                    <th className="py-3 px-4">Employees</th>
                    <th className="py-3 px-4">ICP Fit</th>
                    <th className="py-3 px-4">Timing Signal</th>
                    <th className="py-3 px-4">Key Contact</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181d2a]">
                  {filteredCompanies.map((comp) => (
                    <tr key={comp.id} className="hover:bg-[#131722] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">
                        <div>{comp.name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{comp.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300">
                        <div>{comp.industry}</div>
                        <div className="text-[11px] text-slate-500">{comp.location}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-300">
                        {comp.employeeCount.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 font-bold">
                          {Math.round(comp.fitScore * 100)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300 text-[11px] max-w-xs truncate">
                        {comp.timingSignal}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-white">{comp.keyContactName}</div>
                        <div className="text-[11px] text-slate-400">{comp.keyContactRole}</div>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            // Find contact or switch to emails
                            const contact = filteredContacts.find(
                              (c) => c.domain === comp.domain || c.companyName === comp.name
                            );
                            if (contact) {
                              setActiveContactId(contact.id);
                            }
                            setActiveTab("emails");
                          }}
                          className="px-3 py-1.5 bg-[#00c288] hover:bg-[#00d696] text-slate-950 font-bold rounded-lg text-xs transition-colors"
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
          <div className="h-full bg-[#0e1118] border border-[#1e2434] rounded-xl overflow-hidden shadow-xl flex flex-col">
            <div className="p-4 border-b border-[#1b2130] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Target Decision Makers</h3>
                <p className="text-xs text-slate-400">
                  Verified executive buyers across target accounts with direct waterfall verification.
                </p>
              </div>
              <span className="text-xs font-mono px-2 py-1 bg-[#171c28] rounded border border-[#232a3c] text-slate-300">
                {filteredContacts.length} people identified
              </span>
            </div>

            <div className="flex-1 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#1b2130] bg-[#10141f] text-slate-400 font-semibold text-[11px] uppercase tracking-wider">
                    <th className="py-3 px-4">Decision Maker</th>
                    <th className="py-3 px-4">Role &amp; Company</th>
                    <th className="py-3 px-4">Verified Email</th>
                    <th className="py-3 px-4">Waterfall Providers</th>
                    <th className="py-3 px-4">Fit Score</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181d2a]">
                  {filteredContacts.map((person) => (
                    <tr key={person.id} className="hover:bg-[#131722] transition-colors">
                      <td className="py-3.5 px-4 font-semibold text-white">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-[#1b2232] border border-[#2b354d] flex items-center justify-center font-bold text-[11px] text-white">
                            {person.initials}
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span>{person.name}</span>
                              <a
                                href={person.linkedinUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="w-3.5 h-3.5 bg-blue-600 rounded text-white flex items-center justify-center text-[9px] font-bold"
                              >
                                in
                              </a>
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-300">
                        <div>{person.title}</div>
                        <div className="text-[11px] text-slate-400 font-mono">{person.domain}</div>
                      </td>
                      <td className="py-3.5 px-4 font-mono">
                        {person.email ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-white">{person.email}</span>
                            {person.emailStatus === "catch_all" && (
                              <span className="px-1 py-0.2 bg-amber-950/80 border border-amber-500/40 text-amber-400 text-[9px] rounded">
                                catch_all
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-500 italic text-[11px]">no email found</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1">
                          {person.providers.map((p) => (
                            <span
                              key={p.name}
                              className="px-1.5 py-0.5 rounded text-[10px] bg-[#181e2b] border border-[#242c3d] text-slate-400"
                            >
                              {p.name}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-mono bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 font-bold">
                          {Math.round(person.fitScore * 100)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            setActiveContactId(person.id);
                            setActiveTab("emails");
                          }}
                          className="px-3 py-1.5 bg-[#00c288] hover:bg-[#00d696] text-slate-950 font-bold rounded-lg text-xs transition-colors"
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

      {/* Global Modals */}
      <CompetitorModal />
      <CampaignLaunchModal />
    </div>
  );
}
