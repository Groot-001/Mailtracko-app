import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { AxiosProgressEvent } from 'axios'
import type { Contact, ContactList } from '../types/contacts.types'
import { getApiErrorMessage } from '../../../shared/utils/apiError'
import { Plus, Search, Trash2, Upload, Download, Users, Sparkles, ShieldCheck, Loader2, MoreHorizontal, Pencil } from 'lucide-react'
import { Link, useSearch } from '@tanstack/react-router'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useContacts } from '../hooks/useContacts'
import { useContactLists } from '../hooks/useContactLists'
import { AppSelect } from '../../../shared/components/AppSelect'
import { ConfirmDialog } from '../../../shared/components/ConfirmDialog'
import { DataPreviewTable } from '../../../shared/components/DataPreviewTable'
import { Modal } from '../../../shared/components/Modal'
import { PaginationControls } from '../../../shared/components/PaginationControls'
import { useToast } from '../../../shared/hooks/useToast'
import {
  importContactsCsv,
  createContact as apiCreateContact,
  deleteContact as apiDeleteContact,
  createContactList,
  verifyContactEmail,
  bulkVerifyContactEmails,
  updateContactList,
  deleteContactList,
  getContactListCampaignUsage,
  listContacts,
} from '../api/contactsApi'
import { getPlatformAccess } from '../../platform/api/platformApi'

type CsvRow = string[]

interface ImportFeedback {
  total: number;
  imported: number;
  updated: number;
  errors: Array<{ row: number; error: string }>;
  skipped?: number;
  duplicates?: number;
  reasons?: Record<string, number>;
}

const parseCsvText = (text: string): { headers: string[]; rows: CsvRow[] } => {
  const lines = text.replace(/\r/g, '').split('\n').filter(Boolean)
  if (lines.length === 0) return { headers: [], rows: [] }
  const headers = lines[0].split(',').map(h => h.trim())
  const rows = lines.slice(1).map(l => l.split(',').map(c => c.trim()))
  return { headers, rows }
}

const getInitials = (contact: { email?: string; metadata?: Record<string, string | null> }) => {
  const parts = [contact.metadata?.name, contact.metadata?.first_name, contact.metadata?.last_name, contact.email]
    .filter(Boolean)
    .map((value) => String(value).trim())
  const letters = parts.join(' ').split(/\s+/).filter(Boolean)
  if (letters.length === 0) return 'C'
  return letters.slice(0, 2).map((part) => part[0]?.toUpperCase() ?? '').join('')
}

const autoMapCsvHeaders = (headers: string[]) => {
  return headers.reduce<Record<string, string>>((map, header) => {
    const normalized = header.trim().toLowerCase().replace(/[^a-z0-9]/g, '')
    if (/^(email|e?mail|emailaddress|emailaddr)$/.test(normalized) || normalized.includes('email')) {
      map[header] = 'email'
    } else if (/^(name|fullname|full_name)$/.test(normalized) || normalized.includes('name')) {
      map[header] = 'name'
    } else if (/^(firstname|first_name|givenname|given_name)$/.test(normalized)) {
      map[header] = 'first_name'
    } else if (/^(lastname|last_name|surname)$/.test(normalized)) {
      map[header] = 'last_name'
    }
    return map
  }, {})
}

const csvTemplateHeaders = [
  'email',
  'first_name',
  'last_name',
  'company',
  'phone',
  'city',
  'state',
  'country',
]

const downloadCsvImportTemplate = () => {
  const csvContent = `${csvTemplateHeaders.join(',')}\n`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'contacts-import-template.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export const ContactsDashboard: React.FC = () => {
  const platformAccess = useQuery({
    queryKey: ['platform', 'access'],
    queryFn: getPlatformAccess,
    staleTime: 5 * 60 * 1000,
  })
  const emailVerificationConfigured =
    platformAccess.data?.integrations?.email_verification_configured !== false
  const searchParams: { listUuid?: string } = useSearch({ from: '/_protected/contacts/' })
  const queryClient = useQueryClient()

  const [contactsPage, setContactsPage] = useState(1)
  const [contactsLimit, setContactsLimit] = useState(10)
  const [pendingDeleteContact, setPendingDeleteContact] = useState<Contact | null>(null)
  const [deletingContact, setDeletingContact] = useState(false)

  const [activeListUuid, setActiveListUuid] = useState<string | null>(searchParams.listUuid || null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [verificationFilter, setVerificationFilter] = useState('all')

  const listsQuery = useContactLists(100, 0)
  const lists = listsQuery.data?.items || []
  const listsLoading = listsQuery.isLoading
  const listsError = listsQuery.error ? getApiErrorMessage(listsQuery.error, 'Collections could not be loaded.') : null

  useEffect(() => {
    if (lists.length > 0) {
      setActiveListUuid((current) => current || searchParams.listUuid || lists[0]?.uuid || null)
    }
  }, [lists, searchParams.listUuid])

  const contactsQuery = useContacts(
    activeListUuid || undefined,
    {
      limit: contactsLimit,
      offset: (contactsPage - 1) * contactsLimit,
      search: search.trim() || undefined,
      status: statusFilter === 'all' ? undefined : (statusFilter as any),
      verification_status: verificationFilter === 'all' ? undefined : (verificationFilter as any),
    }
  )

  const contacts = contactsQuery.data?.items || []
  const contactsTotal = contactsQuery.data?.total ?? 0
  const contactsLoading = contactsQuery.isFetching
  const contactsError = contactsQuery.error ? getApiErrorMessage(contactsQuery.error, 'Contacts could not be loaded for this collection.') : null
  const [selectedContactUuids, setSelectedContactUuids] = useState<string[]>([])
  const [selectedContactsByUuid, setSelectedContactsByUuid] = useState<Record<string, Contact>>({})
  const [selectingAllMatching, setSelectingAllMatching] = useState(false)
  const [allMatchingSelected, setAllMatchingSelected] = useState(false)
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [confirmBulkDelete, setConfirmBulkDelete] = useState(false)
  const [addToListUuid, setAddToListUuid] = useState('')
  const [addingToCollection, setAddingToCollection] = useState(false)
  const [collectionMenuUuid, setCollectionMenuUuid] = useState<string | null>(null)
  const [collectionMenuPosition, setCollectionMenuPosition] = useState<{ top: number; left: number } | null>(null)
  const [importMenuOpen, setImportMenuOpen] = useState(false)
  const [editingList, setEditingList] = useState<ContactList | null>(null)
  const [editingListName, setEditingListName] = useState('')
  const [editingListDescription, setEditingListDescription] = useState('')
  const [savingList, setSavingList] = useState(false)
  const [pendingDeleteList, setPendingDeleteList] = useState<ContactList | null>(null)
  const [pendingDeleteCampaignWarning, setPendingDeleteCampaignWarning] = useState<{ list: ContactList; campaigns: Array<{ name: string; status: string }> } | null>(null)
  const [checkingDeleteUsage, setCheckingDeleteUsage] = useState(false)
  const [deletingList, setDeletingList] = useState(false)
  const [verifyingContactUuid, setVerifyingContactUuid] = useState<string | null>(null)
  const [bulkVerifying, setBulkVerifying] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [contactSubmitting, setContactSubmitting] = useState(false)

  const [csvText, setCsvText] = useState('')
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvHeaders, setCsvHeaders] = useState<string[]>([])
  const [csvRows, setCsvRows] = useState<CsvRow[]>([])
  const [headerMap, setHeaderMap] = useState<Record<string, string>>({})
  const [csvPreviewOpen, setCsvPreviewOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [importTargetListUuid, setImportTargetListUuid] = useState<string | null>(null)
  const [showCreateListForm, setShowCreateListForm] = useState(false)
  const [newListName, setNewListName] = useState('')
  const [newListDescription, setNewListDescription] = useState('')
  const [lastImportFeedback, setLastImportFeedback] = useState<ImportFeedback | null>(null)
  const importMenuRef = useRef<HTMLDivElement>(null)
  const csvFileInputRef = useRef<HTMLInputElement>(null)

  const { showToast } = useToast()

  useEffect(() => {
    if (!importMenuOpen) return

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!importMenuRef.current?.contains(event.target as Node)) setImportMenuOpen(false)
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setImportMenuOpen(false)
    }

    document.addEventListener('mousedown', closeOnOutsideClick)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('mousedown', closeOnOutsideClick)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [importMenuOpen])

  useEffect(() => {
    if (!collectionMenuUuid) return
    const close = (event: MouseEvent) => {
      const target = event.target as Element | null
      if (!target?.closest('[data-collection-menu-root="true"]')) {
        setCollectionMenuUuid(null)
        setCollectionMenuPosition(null)
      }
    }
    const escape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setCollectionMenuUuid(null)
        setCollectionMenuPosition(null)
      }
    }
    const closeOnViewportChange = () => {
      setCollectionMenuUuid(null)
      setCollectionMenuPosition(null)
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', escape)
    window.addEventListener('resize', closeOnViewportChange)
    window.addEventListener('scroll', closeOnViewportChange, true)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', escape)
      window.removeEventListener('resize', closeOnViewportChange)
      window.removeEventListener('scroll', closeOnViewportChange, true)
    }
  }, [collectionMenuUuid])



  const filteredContacts = useMemo(() => {
    const query = search.trim().toLowerCase()
    return contacts.filter((contact) => {
      const haystack = [contact.metadata?.name, contact.email, contact.metadata?.first_name, contact.metadata?.last_name, contact.metadata?.company]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      const matchesQuery = !query || haystack.includes(query)
      const matchesStatus = statusFilter === 'all' || contact.status === statusFilter
      const matchesVerification = verificationFilter === 'all' || contact.verification_status === verificationFilter
      return matchesQuery && matchesStatus && matchesVerification
    })
  }, [contacts, search, statusFilter, verificationFilter])

  const contactsTotalPages = Math.max(1, Math.ceil(contactsTotal / contactsLimit))
  useEffect(() => {
    if (contactsPage > contactsTotalPages) setContactsPage(contactsTotalPages)
  }, [contactsPage, contactsTotalPages])

  const activeList = useMemo(() => lists.find((list) => list.uuid === activeListUuid) || null, [lists, activeListUuid])

  const stats = useMemo(() => {
    const total = lists.reduce((sum, list) => sum + (list.contact_count || 0), 0)
    const verified = lists.reduce((sum, list) => sum + (list.verified_count || 0), 0)
    return {
      total,
      verified,
      activeCollectionContacts: activeList?.contact_count ?? contacts.length,
      collections: lists.length,
    }
  }, [activeList?.contact_count, contacts.length, lists])

  const refreshCollections = async () => {
    await queryClient.invalidateQueries({ queryKey: ["contact-lists"] })
  }


  const syncContactsWorkspace = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["contact-lists"] }),
      queryClient.invalidateQueries({ queryKey: ["contacts"] }),
    ])
  }

  const openCsvFilePicker = () => {
    setImportMenuOpen(false)
    csvFileInputRef.current?.click()
  }

  const replaceContacts = async () => {
    await queryClient.invalidateQueries({ queryKey: ["contacts"] })
  }

  const handleVerifyContact = async (contactUuid: string) => {
    if (!activeListUuid) return
    if (!emailVerificationConfigured) {
      showToast('Email verification is not enabled for this MailTracko environment. Contact your administrator.', 'info')
      return
    }
    setVerifyingContactUuid(contactUuid)
    try {
      const updated = await verifyContactEmail(activeListUuid, contactUuid)
      await replaceContacts()
      showToast(`Verification completed: ${updated.verification_status}`, 'success')
    } catch (error: unknown) {
      console.error(error)
      showToast(getApiErrorMessage(error, 'Email verification failed'), 'error')
    } finally {
      setVerifyingContactUuid(null)
    }
  }

  const clearContactSelection = () => {
    setSelectedContactUuids([])
    setSelectedContactsByUuid({})
    setAllMatchingSelected(false)
  }

  const pageContactUuids = filteredContacts.map((contact) => contact.uuid)
  const pageAllSelected = pageContactUuids.length > 0 && pageContactUuids.every((uuid) => selectedContactUuids.includes(uuid))

  const toggleContactSelection = (contact: Contact, checked: boolean) => {
    setAllMatchingSelected(false)
    setSelectedContactUuids((current) => checked
      ? [...new Set([...current, contact.uuid])]
      : current.filter((uuid) => uuid !== contact.uuid))
    setSelectedContactsByUuid((current) => {
      const next = { ...current }
      if (checked) next[contact.uuid] = contact
      else delete next[contact.uuid]
      return next
    })
  }

  const toggleCurrentPageSelection = (checked: boolean) => {
    setAllMatchingSelected(false)
    setSelectedContactUuids((current) => {
      const page = new Set(pageContactUuids)
      return checked ? [...new Set([...current, ...pageContactUuids])] : current.filter((uuid) => !page.has(uuid))
    })
    setSelectedContactsByUuid((current) => {
      const next = { ...current }
      for (const contact of filteredContacts) {
        if (checked) next[contact.uuid] = contact
        else delete next[contact.uuid]
      }
      return next
    })
  }

  const fetchAllMatchingContacts = async (): Promise<Contact[]> => {
    if (!activeListUuid) return []
    const limit = 200
    let offset = 0
    let total: number
    const items: Contact[] = []
    do {
      const page = await listContacts(activeListUuid, {
        limit,
        offset,
        search: search.trim() || undefined,
        status: statusFilter === 'all' ? undefined : statusFilter as Contact['status'],
        verification_status: verificationFilter === 'all' ? undefined : verificationFilter as Contact['verification_status'],
      })
      items.push(...page.items)
      total = page.total
      offset += page.items.length
      if (page.items.length === 0) break
    } while (offset < total)
    return items
  }

  const selectAllMatchingContacts = async () => {
    if (!activeListUuid || contactsTotal === 0) return
    setSelectingAllMatching(true)
    try {
      const matching = await fetchAllMatchingContacts()
      setSelectedContactUuids(matching.map((contact) => contact.uuid))
      setSelectedContactsByUuid(Object.fromEntries(matching.map((contact) => [contact.uuid, contact])))
      setAllMatchingSelected(true)
      showToast(`Selected all ${matching.length} matching contacts.`, 'success')
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Could not select all matching contacts.'), 'error')
    } finally {
      setSelectingAllMatching(false)
    }
  }

  const handleBulkVerify = async () => {
    if (!activeListUuid || selectedContactUuids.length === 0) return
    if (!emailVerificationConfigured) {
      showToast('Email verification is not enabled for this MailTracko environment. Contact your administrator.', 'info')
      return
    }

    setBulkVerifying(true)
    try {
      const updated: Contact[] = []
      for (let index = 0; index < selectedContactUuids.length; index += 200) {
        const result = await bulkVerifyContactEmails(activeListUuid, selectedContactUuids.slice(index, index + 200))
        updated.push(...result.items)
      }
      replaceContacts(updated)
      clearContactSelection()
      showToast(`${updated.length} contacts verified`, 'success')
    } catch (error: unknown) {
      console.error(error)
      showToast(getApiErrorMessage(error, 'Bulk email verification failed'), 'error')
    } finally {
      setBulkVerifying(false)
    }
  }

  const handleExportSelected = async () => {
    if (selectedContactUuids.length === 0) return
    let selected = selectedContactUuids.map((uuid) => selectedContactsByUuid[uuid]).filter(Boolean)
    if (selected.length !== selectedContactUuids.length) {
      try {
        const matching = await fetchAllMatchingContacts()
        const selectedSet = new Set(selectedContactUuids)
        selected = matching.filter((contact) => selectedSet.has(contact.uuid))
      } catch (error: unknown) {
        showToast(getApiErrorMessage(error, 'Could not prepare selected contacts for export.'), 'error')
        return
      }
    }
    const headers = ['email', 'name', 'first_name', 'last_name', 'company', 'status', 'verification_status']
    const escapeCsv = (value: string | null | undefined) => `"${String(value ?? '').replace(/"/g, '""')}"`
    const rows = selected.map((contact) => [
      contact.email,
      contact.metadata?.name,
      contact.metadata?.first_name,
      contact.metadata?.last_name,
      contact.metadata?.company,
      contact.status,
      contact.verification_status,
    ].map(escapeCsv).join(','))
    const blob = new Blob([[headers.join(','), ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `selected-contacts-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    showToast(`Exported ${selected.length} selected contacts.`, 'success')
  }

  const handleBulkDeleteSelected = async () => {
    if (!activeListUuid || selectedContactUuids.length === 0) return
    setBulkDeleting(true)
    try {
      for (let index = 0; index < selectedContactUuids.length; index += 20) {
        await Promise.all(selectedContactUuids.slice(index, index + 20).map((uuid) => apiDeleteContact(activeListUuid, uuid)))
      }
      const count = selectedContactUuids.length
      clearContactSelection()
      setConfirmBulkDelete(false)
      const nextPage = contactsPage > 1 && contacts.length <= count ? contactsPage - 1 : contactsPage
      if (nextPage !== contactsPage) setContactsPage(nextPage)
      await syncContactsWorkspace()
      showToast(`${count} contacts deleted successfully.`, 'success')
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Failed to delete selected contacts.'), 'error')
    } finally {
      setBulkDeleting(false)
    }
  }

  const handleAddSelectedToCollection = async (targetListUuid = addToListUuid) => {
    if (!targetListUuid || selectedContactUuids.length === 0 || addingToCollection) return
    const selected = selectedContactUuids.map((uuid) => selectedContactsByUuid[uuid]).filter(Boolean)
    if (selected.length !== selectedContactUuids.length) {
      showToast('Reload the selection before adding contacts to another collection.', 'info')
      return
    }
    setAddingToCollection(true)
    try {
      let added = 0
      let skipped = 0
      for (const contact of selected) {
        const metadata = Object.fromEntries(Object.entries(contact.metadata || {}).filter((entry): entry is [string, string] => typeof entry[1] === 'string'))
        try {
          await apiCreateContact(targetListUuid, { email: contact.email, metadata })
          added += 1
        } catch {
          skipped += 1
        }
      }
      showToast(`Added ${added} contacts to the collection${skipped ? `; ${skipped} already existed or could not be copied` : ''}.`, skipped ? 'info' : 'success')
      setAddToListUuid('')
      await refreshCollections()
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Could not add the selected contacts to the collection.'), 'error')
    } finally {
      setAddingToCollection(false)
    }
  }

  const handleFileChange = (f?: File) => {
    if (!f) return
    if (f.size > 5 * 1024 * 1024) {
      showToast('CSV files must be 5 MB or smaller.', 'error')
      return
    }
    setCsvFile(f)
    const reader = new FileReader()
    reader.onload = () => {
      const text = String(reader.result || '')
      if (!text.trim()) {
        showToast('The selected file is empty. Choose a CSV file with contact rows.', 'info')
        setCsvFile(null)
        setCsvText('')
        setCsvHeaders([])
        setCsvRows([])
        setHeaderMap({})
        setCsvPreviewOpen(false)
        return
      }
      setCsvText(text)
      const parsed = parseCsvText(text)
      setCsvHeaders(parsed.headers)
      setCsvRows(parsed.rows)
      setHeaderMap(autoMapCsvHeaders(parsed.headers))
      setCsvPreviewOpen(true)
      if (!importTargetListUuid && activeListUuid) {
        setImportTargetListUuid(activeListUuid)
      }
    }
    reader.readAsText(f)
  }

  const updateHeaderMap = (header: string, value: string) => {
    setHeaderMap((prev) => ({ ...prev, [header]: value }))
  }

  const hasEmailMapping = useMemo(() => {
    if (csvHeaders.length === 0) return false
    return csvHeaders.some((header) => {
      const target = (headerMap[header] || header).trim().toLowerCase()
      return target === 'email' || target.includes('email')
    })
  }, [csvHeaders, headerMap])

  const importValidationMessage = useMemo(() => {
    if (!csvFile && !csvText) return 'Choose a CSV file to import contacts.'
    if (csvRows.length === 0) return 'The file has headers but no contact rows to import.'
    if (!hasEmailMapping) return 'Map one header to email before importing.'
    return 'Ready to upload your contacts.'
  }, [csvFile, csvText, csvRows.length, hasEmailMapping])

  const handleCsvConfirmImport = async () => {
    if (!csvFile && !csvText) {
      showToast('Import a CSV file first before confirming', 'info')
      return
    }

    if (csvRows.length === 0) {
      showToast('This file has no contact rows to import.', 'info')
      return
    }

    const targetList = importTargetListUuid || activeListUuid || lists?.[0]?.uuid
    if (!targetList) {
      showToast('Please select a collection to import into', 'info')
      return
    }

    const hasAnyMapping = Object.values(headerMap).some(Boolean)
    let fileToUpload: File

    if (hasAnyMapping) {
      const keepHeaders = csvHeaders.filter((h) => headerMap[h])
      const mappedNames = keepHeaders.map((h) => headerMap[h] || h)
      const hasEmail = mappedNames.map((s) => String(s).toLowerCase()).some((s) => s === 'email' || s.includes('email'))
      if (!hasEmail) {
        showToast('Please map one header to "email" before importing', 'info')
        return
      }

      const escape = (v: string) => '"' + String(v || '').replace(/"/g, '""') + '"'
      const headerLine = mappedNames.join(',')
      const rowLines = csvRows.map((r) => {
        const values: string[] = []
        for (const originalHeader of keepHeaders) {
          const idx = csvHeaders.indexOf(originalHeader)
          values.push(escape(r[idx] ?? ''))
        }
        return values.join(',')
      })
      const fullCsv = [headerLine, ...rowLines].join('\n')
      if (rowLines.length === 0) {
        showToast('This file has no contact rows to import.', 'info')
        return
      }
      fileToUpload = new File([fullCsv], 'import.csv', { type: 'text/csv' })
    } else if (csvFile) {
      fileToUpload = csvFile
    } else {
      fileToUpload = new File([csvText], 'import.csv', { type: 'text/csv' })
    }

    try {
      setUploading(true)
      setUploadProgress(0)
      const result = await importContactsCsv(targetList, fileToUpload, {
        onUploadProgress: (ev: AxiosProgressEvent) => {
          if (ev.total) setUploadProgress(Math.round((ev.loaded * 100) / ev.total))
        },
      })

      const dynamicResult = result as ImportFeedback
      setLastImportFeedback({
        total: result.total,
        imported: result.imported,
        updated: result.updated,
        errors: result.errors,
        skipped: typeof dynamicResult.skipped === 'number' ? dynamicResult.skipped : undefined,
        duplicates: typeof dynamicResult.duplicates === 'number' ? dynamicResult.duplicates : undefined,
        reasons: dynamicResult.reasons,
      })

      setContactsPage(1)
      if (targetList !== activeListUuid) {
        clearContactSelection()
        setActiveListUuid(targetList)
      }
      await syncContactsWorkspace()

      setCsvPreviewOpen(false)
      setCsvFile(null)
      setCsvText('')
      setCsvHeaders([])
      setCsvRows([])
      setHeaderMap({})
      const extraCounts: string[] = []
      if (typeof dynamicResult.skipped === 'number') extraCounts.push(`skipped ${dynamicResult.skipped}`)
      if (typeof dynamicResult.duplicates === 'number') extraCounts.push(`duplicates ${dynamicResult.duplicates}`)
      if (result.updated > 0) extraCounts.push(`updated ${result.updated}`)
      showToast(
        `Import complete: imported ${result.imported} of ${result.total}${extraCounts.length ? ` (${extraCounts.join(', ')})` : ''}`,
        'success',
      )
    } catch (err: unknown) {
      console.error('Import error', err)
      const message = getApiErrorMessage(err, 'Import failed — see console for details')
      showToast(message, 'error')
    } finally {
      setUploading(false)
    }
  }

  const ensureContactListExists = async () => {
    if (activeListUuid) return activeListUuid

    const defaultName = 'My contacts'
    const list = await createContactList(defaultName, 'Auto-created collection')
    await refreshCollections()
    setSelectedContactUuids([])
    setActiveListUuid(list.uuid)
    return list.uuid
  }

  const createContact = async (payload: { name?: string; email?: string }, targetListUuid?: string) => {
    const trimmedEmail = payload.email?.trim() || ''
    const trimmedName = payload.name?.trim() || undefined

    if (!trimmedEmail) {
      showToast('Please enter a valid email address', 'info')
      return false
    }

    let listUuid = targetListUuid || activeListUuid || lists?.[0]?.uuid
    if (!listUuid) {
      try {
        listUuid = await ensureContactListExists()
      } catch (err: unknown) {
        console.error('Create collection failed', err)
        showToast('Please create a contact collection before adding contacts', 'info')
        return false
      }
    }

    try {
      setContactSubmitting(true)
      await apiCreateContact(listUuid, {
        email: trimmedEmail,
        metadata: trimmedName ? { name: trimmedName } : undefined,
      })
      if (listUuid !== activeListUuid) {
        clearContactSelection()
        setActiveListUuid(listUuid)
      }
      setContactsPage(1)
      setShowCreateForm(false)
      await syncContactsWorkspace()
      showToast('Contact created', 'success')
      return true
    } catch (err: unknown) {
      console.error('Create contact failed', err)
      const message = getApiErrorMessage(err, 'Failed to create contact')
      showToast(message, 'error')
      return false
    } finally {
      setContactSubmitting(false)
    }
  }

  const removeContact = async () => {
    const listUuid = activeListUuid || lists?.[0]?.uuid
    if (!listUuid || !pendingDeleteContact) return
    setDeletingContact(true)
    try {
      await apiDeleteContact(listUuid, pendingDeleteContact.uuid)
      setPendingDeleteContact(null)
      const nextPage = contactsPage > 1 && contacts.length <= 1 ? contactsPage - 1 : contactsPage
      if (nextPage !== contactsPage) setContactsPage(nextPage)
      await syncContactsWorkspace()
      showToast('Contact deleted successfully.', 'success')
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Failed to delete contact.'), 'error')
    } finally {
      setDeletingContact(false)
    }
  }

  const openCreateCollection = () => {
    // Always start from a clean controlled form. This also prevents a key used
    // to open the dialog from appearing as stale collection-name state.
    setNewListName('')
    setNewListDescription('')
    setShowCreateListForm(true)
  }

  const createContactListHandler = async () => {
    const trimmedName = newListName.trim()
    if (!trimmedName) {
      showToast('Please give the collection a name', 'info')
      return
    }

    try {
      const list = await createContactList(trimmedName, newListDescription.trim() || undefined)
      clearContactSelection()
      setActiveListUuid(list.uuid)
      setNewListName('')
      setNewListDescription('')
      setShowCreateListForm(false)
      await refreshCollections()
      showToast('Collection created successfully', 'success')
    } catch (err: unknown) {
      console.error('Create collection failed', err)
      showToast(getApiErrorMessage(err, 'Failed to create collection'), 'error')
    }
  }

  const toggleCollectionMenu = (list: ContactList, button: HTMLButtonElement) => {
    if (collectionMenuUuid === list.uuid) {
      setCollectionMenuUuid(null)
      setCollectionMenuPosition(null)
      return
    }

    const rect = button.getBoundingClientRect()
    const menuWidth = 208
    const menuHeight = 104
    const left = Math.max(12, Math.min(window.innerWidth - menuWidth - 12, rect.right - menuWidth))
    const top = window.innerHeight - rect.bottom >= menuHeight + 8
      ? rect.bottom + 8
      : Math.max(12, rect.top - menuHeight - 8)

    setCollectionMenuUuid(list.uuid)
    setCollectionMenuPosition({ top, left })
  }

  const openEditCollection = (list: ContactList) => {
    setCollectionMenuUuid(null)
    setCollectionMenuPosition(null)
    setEditingList(list)
    setEditingListName(list.name)
    setEditingListDescription(list.description || '')
  }

  const saveCollectionChanges = async () => {
    if (!editingList) return
    const name = editingListName.trim()
    if (!name) {
      showToast('Collection name is required.', 'info')
      return
    }
    setSavingList(true)
    try {
      await updateContactList(editingList.uuid, {
        name,
        description: editingListDescription.trim(),
      })
      setEditingList(null)
      await refreshCollections()
      showToast('Collection updated successfully.', 'success')
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Failed to update collection.'), 'error')
    } finally {
      setSavingList(false)
    }
  }

  const prepareDeleteCollection = (list: ContactList) => {
    setCollectionMenuUuid(null)
    setCollectionMenuPosition(null)
    setPendingDeleteList(list)
  }

  const applyDeletedCollection = (deletingUuid: string) => {
    const remaining = lists.filter((list) => list.uuid !== deletingUuid)
    if (activeListUuid === deletingUuid) {
      clearContactSelection()
      setContactsPage(1)
      setActiveListUuid(remaining[0]?.uuid || null)
    }
  }

  const removeCollection = async (list: ContactList, force: boolean) => {
    setDeletingList(true)
    try {
      await deleteContactList(list.uuid, force)
      applyDeletedCollection(list.uuid)
      await refreshCollections()
      setPendingDeleteList(null)
      setPendingDeleteCampaignWarning(null)
      showToast('Collection deleted successfully. Contacts were not individually deleted.', 'success')
    } catch (error: unknown) {
      if (!force) {
        try {
          const usage = await getContactListCampaignUsage(list.uuid)
          if (usage.in_use) {
            setPendingDeleteList(null)
            setPendingDeleteCampaignWarning({
              list,
              campaigns: usage.campaigns.map((campaign) => ({ name: campaign.name, status: campaign.status })),
            })
            return
          }
        } catch {
          // Keep the original deletion error if the follow-up usage check fails.
        }
      }
      showToast(getApiErrorMessage(error, 'Failed to delete collection.'), 'error')
    } finally {
      setDeletingList(false)
    }
  }

  const confirmDeleteCollection = async () => {
    if (!pendingDeleteList) return
    const list = pendingDeleteList
    setCheckingDeleteUsage(true)
    try {
      const usage = await getContactListCampaignUsage(list.uuid)
      if (usage.in_use) {
        setPendingDeleteList(null)
        setPendingDeleteCampaignWarning({
          list,
          campaigns: usage.campaigns.map((campaign) => ({ name: campaign.name, status: campaign.status })),
        })
        return
      }
      await removeCollection(list, false)
    } catch (error: unknown) {
      showToast(getApiErrorMessage(error, 'Could not verify whether this collection is used by a campaign.'), 'error')
    } finally {
      setCheckingDeleteUsage(false)
    }
  }

  const confirmDeleteUsedCollection = async () => {
    if (!pendingDeleteCampaignWarning) return
    await removeCollection(pendingDeleteCampaignWarning.list, true)
  }

  const sheets = useMemo(() => csvRows.slice(0, 100), [csvRows])

  return (
    <>
      <div className="mx-auto max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
      <div className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-700">
              <Sparkles className="h-3.5 w-3.5" /> Contacts workspace
            </div>
            <h1 className="mt-3 text-2xl font-semibold text-stone-900">Manage your contacts clearly</h1>
            <p className="mt-2 max-w-2xl text-sm text-stone-600">
              Create contacts, import CSV or Google Sheets data, and keep every collection ready for campaigns.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={downloadCsvImportTemplate}
              className="inline-flex items-center gap-2 rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm font-medium text-stone-700 transition hover:bg-stone-50"
            >
              <Download className="h-4 w-4" /> Download CSV Template
            </button>
            <div ref={importMenuRef} className="relative">
              <input
                ref={csvFileInputRef}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(event) => {
                  handleFileChange(event.target.files?.[0])
                  event.currentTarget.value = ''
                }}
              />
              <button
                type="button"
                aria-haspopup="menu"
                aria-expanded={importMenuOpen}
                onClick={() => setImportMenuOpen((open) => !open)}
                className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-stone-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-stone-700"
              >
                <Upload className="h-4 w-4" /> Import Contacts
              </button>
              {importMenuOpen ? (
                <div role="menu" className="absolute right-0 z-40 mt-2 w-56 overflow-hidden rounded-xl border border-stone-200 bg-white p-1.5 shadow-xl">
                  <button type="button" role="menuitem" onClick={openCsvFilePicker} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-stone-700 hover:bg-stone-50">
                    <Upload className="h-4 w-4" /> CSV file
                  </button>
                  <Link onClick={() => setImportMenuOpen(false)} to="/contacts/google-sheets" role="menuitem" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50">
                    <Download className="h-4 w-4" /> Google Sheets
                  </Link>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => { setImportMenuOpen(false); setShowCreateForm(true) }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-stone-700 hover:bg-stone-50"
                  >
                    <Plus className="h-4 w-4" /> Manual entry
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
            <p className="text-sm text-stone-600">Total contacts</p>
            <p className="mt-2 text-2xl font-semibold text-stone-900">{stats.total}</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
            <p className="text-sm text-stone-600">Verified emails (optional)</p>
            <p className="mt-2 text-2xl font-semibold text-stone-900">{stats.verified}</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
            <p className="text-sm text-stone-600">Active collection</p>
            <p className="mt-2 text-2xl font-semibold text-stone-900">{stats.activeCollectionContacts}</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
            <p className="text-sm text-stone-600">Collections</p>
            <p className="mt-2 text-2xl font-semibold text-stone-900">{stats.collections}</p>
          </div>
        </div>

        {listsError && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
            {listsError} Refresh the page or try again after confirming the API is available.
          </div>
        )}
        {contactsError && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" role="alert">
            {contactsError}
          </div>
        )}

        {lastImportFeedback && (
          <div className="mt-4 rounded-2xl border border-stone-200 bg-stone-50 p-4">
            <p className="text-sm font-semibold text-stone-900">Latest import summary</p>
            <div className="mt-3 grid gap-2 text-xs text-stone-700 sm:grid-cols-4">
              <p>Total: <span className="font-semibold">{lastImportFeedback.total}</span></p>
              <p>Imported: <span className="font-semibold">{lastImportFeedback.imported}</span></p>
              <p>Updated: <span className="font-semibold">{lastImportFeedback.updated}</span></p>
              <p>Errors: <span className="font-semibold">{lastImportFeedback.errors.length}</span></p>
              {typeof lastImportFeedback.skipped === 'number' && <p>Skipped: <span className="font-semibold">{lastImportFeedback.skipped}</span></p>}
              {typeof lastImportFeedback.duplicates === 'number' && <p>Duplicates: <span className="font-semibold">{lastImportFeedback.duplicates}</span></p>}
            </div>
            {lastImportFeedback.reasons && Object.keys(lastImportFeedback.reasons).length > 0 && (
              <div className="mt-3 rounded-xl border border-stone-200 bg-white p-3">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-stone-600">Reasons</p>
                <div className="mt-2 grid gap-1 text-xs text-stone-700">
                  {Object.entries(lastImportFeedback.reasons).map(([reason, count]) => (
                    <p key={reason}>{reason}: <span className="font-semibold">{count}</span></p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-stone-900">
              <Users className="h-4 w-4" /> Quick actions
            </div>
            <p className="mt-2 text-sm text-stone-600">
              Import one batch at a time and keep each collection ready for campaigns.
            </p>
            <p className="mt-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Email verification is optional. Unverified contacts can still be included in bulk campaigns; verification is available when you want an extra deliverability check.
            </p>
            <div className="mt-4 space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-stone-700">Collections</p>
                    <p className="mt-1 text-xs text-stone-500">
                      Choose one collection as the target for contact management and imports.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={openCreateCollection}
                    className="rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-300"
                  >
                    Create collection
                  </button>
                </div>

                {listsLoading ? (
                  <div className="flex items-center gap-2 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm text-stone-600">
                    <Loader2 className="h-4 w-4 animate-spin" /> Loading collections…
                  </div>
                ) : listsError ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-800">
                    Collections are unavailable right now.
                  </div>
                ) : lists.length > 0 ? (
                  <div className="max-h-[360px] space-y-2 overflow-y-auto overscroll-contain pr-1" aria-label="Collections">
                    {lists.map((list) => (
                      <div
                        key={list.uuid}
                        data-collection-menu-root="true"
                        className={`relative min-w-0 rounded-2xl border text-sm transition ${
                          list.uuid === activeListUuid
                            ? 'border-amber-400 bg-amber-50 text-stone-900'
                            : 'border-stone-200 bg-white text-stone-700 hover:border-stone-300 hover:bg-stone-50'
                        }`}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            clearContactSelection()
                            setContactsPage(1)
                            setActiveListUuid(list.uuid)
                          }}
                          className="block w-full min-w-0 rounded-2xl px-3 py-3 pr-11 text-left"
                        >
                          <div className="flex min-w-0 items-center justify-between gap-2">
                            <p className="min-w-0 flex-1 truncate font-medium" title={list.name}>{list.name}</p>
                            <span className="shrink-0 rounded-full bg-stone-100 px-2 py-0.5 text-[10px] font-semibold text-stone-600">
                              {list.contact_count || 0} contacts
                            </span>
                          </div>
                          <p className="mt-0.5 line-clamp-2 break-words text-xs text-stone-500" title={list.description || 'No description'}>{list.description || 'No description'}</p>
                          <p className="mt-1 text-[11px] text-stone-500">{list.verified_count || 0} verified</p>
                        </button>
                        <button
                          type="button"
                          aria-label={`Collection actions for ${list.name}`}
                          aria-haspopup="menu"
                          aria-expanded={collectionMenuUuid === list.uuid}
                          onClick={(event) => toggleCollectionMenu(list, event.currentTarget)}
                          className="absolute right-2 top-2 rounded-lg p-2 text-stone-500 transition hover:bg-white hover:text-stone-900 focus:outline-none focus:ring-2 focus:ring-amber-300"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-4 text-sm text-stone-600">
                    Start by creating a collection to add your first contacts.
                  </div>
                )}
              </div>

            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              <button
              type="button"
              onClick={() => {
                if (csvFile || csvText) setCsvPreviewOpen(true)
                else openCsvFilePicker()
              }}
              className="w-full rounded-xl border border-stone-200 px-3 py-2 text-sm font-medium text-stone-700 transition hover:bg-stone-50"
            >
              Import CSV
              </button>
              <Link
                to="/contacts/google-sheets"
                className="inline-flex w-full items-center justify-center rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm font-medium text-stone-700 transition hover:bg-stone-50"
              >
                Import from Google Sheets
              </Link>
            </div>
          </div>

        </aside>

        <section className="space-y-4">
          <div className="rounded-3xl border border-stone-200 bg-white p-4 shadow-sm">
            <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_180px_190px]">
              <label className="flex cursor-text items-center gap-2 rounded-2xl border border-stone-200 bg-stone-50 px-3 py-2 text-sm text-stone-600 transition focus-within:border-[#8F740D] focus-within:bg-white focus-within:ring-2 focus-within:ring-[#F1D442]/30">
                <Search className="h-4 w-4" />
                <input
                  value={search}
                  maxLength={100}
                  onChange={(event) => { setSearch(event.target.value); setContactsPage(1) }}
                  placeholder="Search name, email, company, or tag"
                  className="w-full border-none bg-transparent outline-none"
                />
              </label>
              <AppSelect value={statusFilter} onValueChange={(value) => { setStatusFilter(value); setContactsPage(1) }} ariaLabel="Contact status" options={[{ value: "all", label: "All contact statuses" }, { value: "active", label: "Active" }, { value: "bounced", label: "Bounced" }, { value: "unsubscribed", label: "Unsubscribed" }, { value: "suppressed", label: "Suppressed" }, { value: "archived", label: "Archived" }]} />
              <AppSelect value={verificationFilter} onValueChange={(value) => { setVerificationFilter(value); setContactsPage(1) }} ariaLabel="Verification status" options={[{ value: "all", label: "All verification results" }, { value: "unverified", label: "Unverified" }, { value: "valid", label: "Valid" }, { value: "invalid", label: "Invalid" }, { value: "catch-all", label: "Catch-all" }, { value: "unknown", label: "Unknown" }, { value: "spamtrap", label: "Spam trap" }, { value: "abuse", label: "Abuse" }, { value: "do_not_mail", label: "Do not mail" }]} />
            </div>
          </div>

          {showCreateForm && <CreateContactForm onCreate={createContact} lists={lists} submitting={contactSubmitting} />}

          <div className="rounded-3xl border border-stone-200 bg-white p-4 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-stone-900">Contacts</h2>
                <p className="text-sm text-stone-600">{contactsTotal} matching contacts</p>
              </div>
              <label className="inline-flex items-center gap-2 rounded-xl border border-stone-200 bg-stone-50 px-3 py-2 text-xs font-semibold text-stone-700">
                <input
                  type="checkbox"
                  checked={pageAllSelected}
                  onChange={(event) => toggleCurrentPageSelection(event.target.checked)}
                  disabled={filteredContacts.length === 0 || contactsLoading}
                  className="h-4 w-4 accent-[#8F740D]"
                />
                Select all on this page
              </label>
            </div>

            {selectedContactUuids.length > 0 ? (
              <div className="mb-4 rounded-2xl border border-amber-200 bg-amber-50 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="mr-auto text-sm font-semibold text-stone-900">
                    {selectedContactUuids.length} selected{allMatchingSelected ? ' · all matching contacts' : ''}
                  </span>
                  <button type="button" disabled={bulkVerifying || !emailVerificationConfigured} onClick={handleBulkVerify} className="inline-flex items-center gap-2 rounded-xl bg-[#8F740D] px-3 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50">
                    {bulkVerifying ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                    Verify selected
                  </button>
                  <button type="button" onClick={handleExportSelected} className="inline-flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs font-semibold text-stone-700 hover:bg-stone-50">
                    <Download className="h-4 w-4" /> Export CSV
                  </button>
                  <AppSelect
                    value={addToListUuid}
                    onValueChange={(value) => {
                      setAddToListUuid(value)
                      if (value) void handleAddSelectedToCollection(value)
                    }}
                    disabled={addingToCollection}
                    ariaLabel="Add selected contacts to collection"
                    searchable
                    className="min-w-48"
                    placeholder={addingToCollection ? 'Adding…' : 'Add to collection…'}
                    options={[{ value: '', label: addingToCollection ? 'Adding…' : 'Add to collection…' }, ...lists.filter((list) => list.uuid !== activeListUuid).map((list) => ({ value: list.uuid, label: list.name }))]}
                  />
                  <button type="button" onClick={() => setConfirmBulkDelete(true)} className="inline-flex items-center gap-2 rounded-xl border border-red-200 bg-white px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50">
                    <Trash2 className="h-4 w-4" /> Delete selected
                  </button>
                  <button type="button" onClick={clearContactSelection} className="rounded-xl px-3 py-2 text-xs font-semibold text-stone-600 hover:bg-white">Clear</button>
                </div>
                {pageAllSelected && !allMatchingSelected && selectedContactUuids.length < contactsTotal ? (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-amber-200 pt-3 text-xs text-stone-700">
                    <span>All {filteredContacts.length} contacts on this page are selected.</span>
                    <button type="button" disabled={selectingAllMatching} onClick={selectAllMatchingContacts} className="font-bold text-[#7A6208] underline underline-offset-2 disabled:opacity-60">
                      {selectingAllMatching ? 'Selecting…' : `Select all ${contactsTotal} matching contacts`}
                    </button>
                  </div>
                ) : null}
              </div>
            ) : null}

            <div className="min-h-[680px]">
            {contactsLoading ? (
                  <div className="flex min-h-48 items-center justify-center gap-2 text-sm text-stone-600"><Loader2 className="h-4 w-4 animate-spin" /> Loading contacts…</div>
                ) : contactsError ? (
                  <div className="min-h-48 rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">{contactsError}</div>
                ) : filteredContacts.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 py-8 text-center text-sm text-stone-600">
                {activeListUuid ? (
                  <>
                    <p className="font-semibold text-stone-900">No contacts yet in this collection.</p>
                    <p className="mt-2">Add a contact or import a CSV to start building your audience.</p>
                    <div className="mt-4 flex flex-col items-center justify-center gap-2 sm:flex-row sm:justify-center">
                      <button
                        type="button"
                        onClick={() => setShowCreateForm(true)}
                        className="rounded-xl bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
                      >
                        Add contact
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          if (csvFile || csvText) setCsvPreviewOpen(true)
                          else openCsvFilePicker()
                        }}
                        className="rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
                      >
                        Import CSV
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="font-semibold text-stone-900">No collection selected.</p>
                    <p className="mt-2">Select or create a collection to view and manage contacts.</p>
                  </>
                )}
              </div>
            ) : (
              <ul className="space-y-3">
                {filteredContacts.map((contact) => (
                  <li key={contact.uuid} className="flex h-[88px] items-center justify-between overflow-hidden rounded-2xl border border-stone-200 bg-stone-50 px-3 py-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedContactUuids.includes(contact.uuid)}
                        onChange={(event) => toggleContactSelection(contact, event.target.checked)}
                        aria-label={`Select ${contact.email}`}
                        className="h-4 w-4 accent-[#8F740D]"
                      />
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-white">
                        {getInitials(contact)}
                      </div>
                      <div className="min-w-0">
                        <p className="max-w-[32rem] truncate text-sm font-semibold text-stone-900">{contact.metadata?.name || contact.email || 'Unnamed contact'}</p>
                        <p className={`max-w-[32rem] truncate text-sm text-stone-600 ${contact.metadata?.name && contact.email ? '' : 'invisible'}`}>{contact.metadata?.name && contact.email ? contact.email : 'placeholder'}</p>
                        <div className="mt-1 flex flex-wrap gap-1.5">
                          <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold uppercase text-stone-600">{contact.status || 'active'}</span>
                          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${contact.verification_status === 'valid' ? 'bg-emerald-100 text-emerald-800' : contact.verification_status === 'unverified' ? 'bg-stone-200 text-stone-600' : 'bg-amber-100 text-amber-800'}`}>
                            {contact.verification_status || 'unverified'}{contact.verification_score != null ? ` · ${contact.verification_score}` : ''}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button type="button" disabled={verifyingContactUuid === contact.uuid || !emailVerificationConfigured} onClick={() => handleVerifyContact(contact.uuid)} className="rounded-full p-2 text-stone-500 transition hover:bg-white hover:text-[#8F740D] disabled:opacity-50" aria-label={`Verify ${contact.email}`}>
                        {verifyingContactUuid === contact.uuid ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => setPendingDeleteContact(contact)}
                        className="rounded-full p-2 text-stone-500 transition hover:bg-white hover:text-red-600"
                        aria-label="Delete contact"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            </div>
            {contactsTotal > 0 ? (
              <PaginationControls
                page={contactsPage}
                pageSize={contactsLimit}
                total={contactsTotal}
                itemLabel="contacts"
                onPageChange={setContactsPage}
                onPageSizeChange={(value) => { setContactsLimit(value); setContactsPage(1) }}
                isLoading={contactsLoading}
                className="mt-4 border-t border-stone-200 pt-4"
              />
            ) : null}
          </div>
        </section>
      </div>

      <ConfirmDialog open={pendingDeleteContact !== null} onOpenChange={(open) => { if (!open && !deletingContact) setPendingDeleteContact(null) }} title="Delete contact?" description={`${pendingDeleteContact?.email ?? "This contact"} will be removed from the active collection.`} confirmLabel="Delete contact" isLoading={deletingContact} onConfirm={removeContact} />

      <ConfirmDialog
        open={pendingDeleteList !== null}
        onOpenChange={(open) => {
          if (!open && !checkingDeleteUsage && !deletingList) setPendingDeleteList(null)
        }}
        title="Delete Collection?"
        description={`Remove ${pendingDeleteList?.name ?? 'this collection'} from the workspace? This action does not issue delete requests for the individual contacts.`}
        confirmLabel="Delete Collection"
        isLoading={checkingDeleteUsage || deletingList}
        onConfirm={confirmDeleteCollection}
      />

      <ConfirmDialog
        open={pendingDeleteCampaignWarning !== null}
        onOpenChange={(open) => {
          if (!open && !deletingList) setPendingDeleteCampaignWarning(null)
        }}
        title="This collection is being used by a campaign"
        description={pendingDeleteCampaignWarning
          ? `This contact collection is currently being used by ${pendingDeleteCampaignWarning.campaigns.length || 'one or more'} unfinished campaign${pendingDeleteCampaignWarning.campaigns.length === 1 ? '' : 's'}${pendingDeleteCampaignWarning.campaigns.length ? ` (${pendingDeleteCampaignWarning.campaigns.map((campaign) => `${campaign.name} - ${campaign.status}`).join(', ')})` : ''}. If you delete it, those campaigns may stop working or fail to send emails. Are you sure you want to delete it anyway?`
          : ''}
        confirmLabel="Delete Anyway"
        isLoading={deletingList}
        onConfirm={confirmDeleteUsedCollection}
      />

      <ConfirmDialog
        open={confirmBulkDelete}
        onOpenChange={(open) => { if (!bulkDeleting) setConfirmBulkDelete(open) }}
        title="Delete selected contacts?"
        description={`${selectedContactUuids.length} selected contacts will be removed from the active collection. This cannot be undone.`}
        confirmLabel="Delete selected"
        isLoading={bulkDeleting}
        onConfirm={handleBulkDeleteSelected}
      />

      <Modal
        open={showCreateListForm}
        title="Create collection"
        description="Create a collection for contacts, imports, and campaign audiences."
        onClose={() => {
          setShowCreateListForm(false)
          setNewListName('')
          setNewListDescription('')
        }}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-stone-700" htmlFor="new-collection-name">Collection name</label>
            <input
              id="new-collection-name"
              data-autofocus="true"
              value={newListName}
              maxLength={50}
              onChange={(event) => setNewListName(event.target.value)}
              placeholder="e.g. Newsletter leads"
              className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:border-[#8F740D] focus:ring-1 focus:ring-[#F1D442]/30"
            />
            <div className="mt-1 flex justify-between text-[11px] text-stone-500"><span>Maximum 50 characters</span><span>{newListName.length}/50</span></div>
          </div>
          <div>
            <label className="text-sm font-medium text-stone-700" htmlFor="new-collection-description">Description</label>
            <textarea
              id="new-collection-description"
              value={newListDescription}
              maxLength={500}
              onChange={(event) => setNewListDescription(event.target.value)}
              rows={4}
              placeholder="Optional description"
              className="mt-2 w-full resize-none rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:border-[#8F740D] focus:ring-1 focus:ring-[#F1D442]/30"
            />
            <div className="mt-1 text-right text-[11px] text-stone-500">{newListDescription.length}/500</div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowCreateListForm(false); setNewListName(''); setNewListDescription('') }} className="rounded-xl border border-stone-200 px-4 py-2 text-sm font-semibold text-stone-700">Cancel</button>
            <button type="button" disabled={!newListName.trim()} onClick={createContactListHandler} className="rounded-xl bg-stone-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">Create collection</button>
          </div>
        </div>
      </Modal>

      {collectionMenuUuid && collectionMenuPosition ? createPortal((() => {
        const menuList = lists.find((list) => list.uuid === collectionMenuUuid)
        if (!menuList) return null
        return (
          <div
            data-collection-menu-root="true"
            role="menu"
            style={{ position: 'fixed', top: collectionMenuPosition.top, left: collectionMenuPosition.left }}
            className="z-[90] w-52 rounded-xl border border-stone-200 bg-white p-1.5 shadow-xl"
          >
            <button type="button" role="menuitem" onClick={() => openEditCollection(menuList)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-stone-700 hover:bg-stone-50">
              <Pencil className="h-4 w-4" /> Rename / Edit Description
            </button>
            <button type="button" role="menuitem" onClick={() => void prepareDeleteCollection(menuList)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50">
              <Trash2 className="h-4 w-4" /> Delete Collection
            </button>
          </div>
        )
      })(), document.body) : null}

      <Modal
        open={editingList !== null}
        title="Edit collection"
        description="Rename the collection or update its description. Changes appear immediately after the server confirms the update."
        onClose={() => { if (!savingList) setEditingList(null) }}
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-stone-700">Collection name</label>
            <input value={editingListName} maxLength={50} onChange={(event) => setEditingListName(event.target.value)} className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-300" />
            <p className="mt-1 text-right text-[11px] text-stone-500">{editingListName.length}/50</p>
          </div>
          <div>
            <label className="text-sm font-medium text-stone-700">Description</label>
            <textarea value={editingListDescription} maxLength={500} onChange={(event) => setEditingListDescription(event.target.value)} rows={4} className="mt-2 w-full resize-none rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-amber-300" />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" disabled={savingList} onClick={() => setEditingList(null)} className="rounded-xl border border-stone-200 px-4 py-2 text-sm font-semibold text-stone-700">Cancel</button>
            <button type="button" disabled={savingList || !editingListName.trim()} onClick={saveCollectionChanges} className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">
              {savingList ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {savingList ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </div>
      </Modal>

      {csvPreviewOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-stone-950/50 p-4 sm:p-6">
          <div className="mt-csv-preview w-full max-w-4xl rounded-3xl border border-stone-200 bg-white p-5 shadow-xl relative z-60 pointer-events-auto max-h-[85vh] overflow-auto" role="dialog" aria-modal="true">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-stone-900">CSV import preview</h3>
                <p className="text-sm text-stone-600">Map headers and choose the collection for this import.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <AppSelect
                  value={importTargetListUuid || ''}
                  onValueChange={(value) => setImportTargetListUuid(value || null)}
                  ariaLabel="Import target collection"
                  searchable
                  className="min-w-52"
                  options={[{ value: "", label: "Select collection" }, ...lists.map((list: ContactList) => ({ value: list.uuid, label: list.name }))]}
                />
                <button type="button" onClick={() => setCsvPreviewOpen(false)} className="rounded-xl border border-stone-200 px-3 py-2 text-sm font-medium text-stone-700">
                  Close
                </button>
              </div>
            </div>

            <div className="mt-4 rounded-2xl border border-stone-200 bg-stone-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-stone-900">Header mapping</p>
                    <p className="mt-1 text-sm text-stone-600">Ensure one column maps to email to avoid import validation errors.</p>
                  </div>
                  <div className="text-sm font-medium text-amber-700">
                    {hasEmailMapping ? 'Email mapped' : 'Email not mapped'}
                  </div>
                </div>
                {csvHeaders.map((header) => (
                  <div key={header} className="rounded-2xl border border-stone-200 bg-white p-3">
                    <p className="text-sm font-medium text-stone-700">{header}</p>
                    <input
                      maxLength={64}
                      className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 outline-none focus:border-[#8F740D]"
                      placeholder="Map to email, name, or first_name"
                      value={headerMap[header] || ''}
                      onChange={(event) => updateHeaderMap(header, event.target.value)}
                    />
                  </div>
                ))}
              </div>

            <div className="mt-4">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#756F60]">
                Imported data preview
              </p>
              <DataPreviewTable headers={csvHeaders} rows={sheets} />
            </div>

            <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
              <div className={`mr-auto text-sm ${hasEmailMapping ? 'text-stone-600' : 'text-red-600'}`}>
                {uploading ? `Uploading ${uploadProgress}%` : importValidationMessage}
              </div>
              <button type="button" onClick={() => setCsvPreviewOpen(false)} className="rounded-xl border border-stone-200 px-3 py-2 text-sm font-medium text-stone-700">
                Cancel
              </button>
              <button type="button" onClick={handleCsvConfirmImport} disabled={uploading || !hasEmailMapping} className="rounded-xl bg-stone-900 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60">
                Import
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  </>
  )
}

const CreateContactForm: React.FC<{ onCreate: (payload: { name?: string; email?: string }, listUuid?: string) => Promise<boolean>; lists?: ContactList[]; submitting?: boolean }> = ({ onCreate, lists = [], submitting = false }) => {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedList, setSelectedList] = useState<string | null>(null)

  // Keep only an explicit user selection that still exists.
  const effectiveSelectedList = selectedList && lists.some((list) => list.uuid === selectedList)
    ? selectedList
    : null

  return (
    <form
      onSubmit={async (event) => {
        event.preventDefault()
        if (!effectiveSelectedList) return
        const created = await onCreate({ name, email }, effectiveSelectedList)
        if (created) {
          setName('')
          setEmail('')
        }
      }}
      className="rounded-3xl border border-stone-200 bg-white p-4 shadow-sm"
    >
      <div className="grid gap-3 md:grid-cols-[auto_1fr_1fr_auto] items-center">
        {lists.length > 0 ? (
          <AppSelect
            value={effectiveSelectedList ?? ''}
            onValueChange={(value) => setSelectedList(value || null)}
            ariaLabel="Contact list"
            searchable
            options={[{ value: "", label: "Select a contact list", disabled: true }, ...lists.map((list: ContactList) => ({ value: list.uuid, label: list.name }))]}
          />
        ) : (
          <div className="text-sm text-stone-500">No collections — create one to add contacts</div>
        )}
        <input
          value={name}
          maxLength={50}
          onChange={(event) => setName(event.target.value)}
          placeholder="Name"
          className="rounded-2xl border border-stone-200 px-3 py-2 text-sm outline-none"
        />
        <input
          type="email"
          value={email}
          maxLength={254}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Email"
          className="rounded-2xl border border-stone-200 px-3 py-2 text-sm outline-none"
        />
        <button
          type="submit"
          disabled={submitting || !effectiveSelectedList}
          className="rounded-2xl bg-stone-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? 'Saving...' : 'Save'}
        </button>
      </div>
    </form>
  )
}

export default ContactsDashboard
