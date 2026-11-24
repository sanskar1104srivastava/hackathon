/** Hindi UI text. Draft wording, to be reviewed by a Hindi speaker before the demo. */
import type { Colour, Domain, ReferralStatus, Setting } from '../api/types'

export const colourLabels: Record<Colour, string> = {
  green: 'ठीक',
  yellow: 'नज़र रखनी है',
  red: 'डॉक्टर को दिखाना है',
}

export const domainLabels: Record<Domain, string> = {
  defects: 'जन्म से जुड़ी समस्याएँ',
  deficiencies: 'पोषण और ख़ून की कमी',
  diseases: 'बीमारियाँ',
  development: 'विकास: बोलना, चलना, सीखना',
}

export const settingLabels: Record<Setting, string> = {
  home: 'घर पर',
  anganwadi: 'आँगनवाड़ी',
  school: 'स्कूल',
  facility: 'अस्पताल',
}

export const referralStatusLabels: Record<ReferralStatus, string> = {
  sent: 'अस्पताल जाना बाक़ी',
  reached: 'अस्पताल पहुँचे',
  underTreatment: 'इलाज चल रहा है',
}

export const text = {
  appTitle: 'बाल स्वास्थ्य जाँच',
  appSubtitle: 'चारों D की जाँच: जन्म दोष, कमी, बीमारी, विकास',
  loading: 'लोड हो रहा है…',
  retry: 'फिर से कोशिश करें',
  back: 'वापस',
  next: 'आगे',
  save: 'सेव करें',
  yes: 'हाँ',
  no: 'नहीं',
  listen: 'सुनें',
  offline: 'इंटरनेट नहीं है',
  pendingSync: (count: number) => `${count} जाँच भेजनी बाक़ी`,

  roles: {
    title: 'आप कौन हैं?',
    field: 'आशा / आँगनवाड़ी / मोबाइल हेल्थ टीम',
    fieldHint: 'बच्चों की जाँच करें',
    doctor: 'डॉक्टर (DEIC / अस्पताल)',
    doctorHint: 'रेफ़र हुए बच्चे देखें',
    dashboard: 'स्वास्थ्य विभाग',
    dashboardHint: 'ज़िले और ब्लॉक के आँकड़े',
  },

  area: {
    district: 'ज़िला',
    block: 'ब्लॉक',
    chooseDistrict: 'ज़िला चुनें',
    chooseBlock: 'ब्लॉक चुनें',
  },

  children: {
    title: 'बच्चे',
    register: 'नया बच्चा जोड़ें',
    alerts: 'आशा के काम',
    empty: 'इस ब्लॉक में अभी कोई बच्चा नहीं जुड़ा है।',
    years: (months: number) =>
      months < 24 ? `${Math.floor(months)} महीने` : `${Math.floor(months / 12)} साल`,
  },

  register: {
    title: 'नया बच्चा जोड़ें',
    name: 'बच्चे का नाम',
    sex: 'लिंग',
    male: 'लड़का',
    female: 'लड़की',
    dateOfBirth: 'जन्म तारीख़',
    guardianName: 'माता-पिता का नाम',
    guardianPhone: 'माता-पिता का मोबाइल नंबर',
    abhaAddress: 'ABHA पता (अगर है)',
    submit: 'जोड़ें',
    needsInternet: 'नया बच्चा जोड़ने के लिए इंटरनेट चाहिए।',
  },

  childDetail: {
    startScreening: 'जाँच शुरू करें',
    history: 'पिछली जाँचें',
    noScreenings: 'अभी कोई जाँच नहीं हुई।',
    parentLink: 'माता-पिता के लिए QR कोड',
    parentLinkHint: 'माता-पिता इसे अपने फ़ोन से स्कैन करें, रोज़ के खेल और सलाह यहीं मिलेंगे।',
    referrals: 'रेफ़रल',
    homePlan: 'घर के खेल चल रहे हैं',
  },

  screening: {
    stepOf: (step: number, total: number) => `चरण ${step} / ${total}`,
    consentTitle: 'माता-पिता की सहमति',
    consentBody:
      'जाँच के लिए बच्चे की फ़ोटो, छोटा वीडियो और आवाज़ रिकॉर्ड की जाएगी। ये सिर्फ़ जाँच के लिए इस्तेमाल होंगी। क्या माता-पिता सहमत हैं?',
    consentYes: 'हाँ, सहमत हैं',
    consentNo: 'नहीं, बिना फ़ोटो के जाँच करें',
    setting: 'जाँच कहाँ हो रही है?',
    measurementsTitle: 'माप',
    readFromPhoto: 'मशीन की फ़ोटो से पढ़ें',
    reading: 'पढ़ रहे हैं…',
    unreadable: 'फ़ोटो से नंबर साफ़ नहीं पढ़ा गया, ख़ुद लिखें।',
    takePhoto: 'फ़ोटो लें',
    takeVideo: 'वीडियो लें',
    checking: 'AI जाँच कर रहा है…',
    aiOffline: 'इंटरनेट नहीं है। आपने जो देखा वह चुनें:',
    outcomeSeen: 'निशान दिखे',
    outcomeNotSeen: 'निशान नहीं दिखे',
    outcomeUnsure: 'पक्का नहीं',
    retake: 'फिर से लें',
    skip: 'छोड़ें',
    speechTitle: 'चित्र पहचानो',
    record: 'रिकॉर्ड शुरू करें',
    stopRecording: 'रिकॉर्ड बंद करें',
    namedCount: (named: number, shown: number) => `${shown} में से ${named} नाम बोले`,
    developmentTitle: 'विकास के सवाल',
    behaviourTitle: 'व्यवहार के सवाल',
    healthTitle: 'स्वास्थ्य के सवाल',
    visionTitle: 'आँखों की जाँच',
    visionHint: 'बच्चा 3 मीटर दूर खड़ा हो। बच्चा हाथ से जो दिशा बताए, वही बटन दबाएँ।',
    attentionTitle: 'ध्यान का खेल',
    attentionHint: 'बच्चा हरा गोला दिखने पर स्क्रीन छुए, लाल दिखने पर न छुए।',
    startGame: 'खेल शुरू करें',
    passed: 'ठीक रहा',
    notPassed: 'ठीक नहीं रहा',
    submit: 'जाँच पूरी करें',
    submitting: 'नतीजा बन रहा है…',
    queued: 'इंटरनेट नहीं है। जाँच फ़ोन में सेव है और इंटरनेट आते ही भेज दी जाएगी।',
  },

  result: {
    title: 'जाँच का नतीजा',
    referralTitle: 'रेफ़रल पर्ची',
    goTo: 'कहाँ जाएँ',
    why: 'क्यों',
    homePlanTitle: 'घर के खेल शुरू',
    homePlanBody: 'माता-पिता को WhatsApp पर रोज़ के खेल भेजे जाएँगे।',
    noDiagnosis: 'यह जाँच कोई बीमारी तय नहीं करती। बीमारी और इलाज डॉक्टर ही तय करते हैं।',
    done: 'बच्चों की सूची पर जाएँ',
  },

  alerts: {
    title: 'आशा के काम',
    empty: 'अभी कोई काम बाक़ी नहीं है।',
    close: 'काम हो गया',
    kinds: {
      noImprovement: 'दोबारा जाँच करें',
      referralNotReached: 'रेफ़रल पर ध्यान दें',
      callbackRequested: 'परिवार को फ़ोन करें',
    },
  },

  doctor: {
    title: 'रेफ़र हुए बच्चे',
    facility: 'अस्पताल / DEIC',
    empty: 'इस अस्पताल में अभी कोई रेफ़रल नहीं है।',
    markArrived: 'बच्चा अस्पताल पहुँच गया',
    diagnosisTitle: 'जाँच और इलाज दर्ज करें',
    doctorName: 'डॉक्टर का नाम',
    diagnosis: 'डॉक्टर की राय (diagnosis)',
    careInstructions: 'परिवार के लिए सलाह (हिंदी में)',
    medicineName: 'दवा का नाम',
    medicineSchedule: 'कब देनी है',
    checkupDate: 'अगली जाँच की तारीख़',
    therapyDate: 'थेरेपी की तारीख़',
    saveDiagnosis: 'इलाज शुरू करें',
    recordsTitle: 'ABDM से जाँच रिकॉर्ड',
    requesterName: 'डॉक्टर का नाम',
    requesterId: 'HPR ID',
    requestRecords: 'सहमति माँगें',
    refreshRecords: 'स्थिति देखें',
    noAbha: 'इस बच्चे का ABHA नहीं जुड़ा है।',
  },

  dashboard: {
    title: 'स्वास्थ्य विभाग डैशबोर्ड',
    subtitle: 'सिर्फ़ गिनती दिखती है, किसी बच्चे की निजी जानकारी नहीं।',
    state: 'पूरा उत्तर प्रदेश',
    district: 'ज़िला',
    skipWeek: 'डेमो: एक हफ़्ता आगे बढ़ाएँ',
    counters: {
      screened: 'जाँच हुई',
      flaggedDefects: 'जन्म दोष',
      flaggedDeficiencies: 'कमी',
      flaggedDiseases: 'बीमारी',
      flaggedDevelopment: 'विकास',
      referred: 'रेफ़र हुए',
      reached: 'अस्पताल पहुँचे',
      homePlans: 'घर के खेल',
      improving: 'सुधार',
      alerts: 'आशा अलर्ट',
    },
  },

  parent: {
    greeting: (name: string) => `${name} के लिए`,
    latestResult: 'आख़िरी जाँच का नतीजा',
    todaysActivities: 'आज के खेल',
    done: 'हो गया',
    doneThanks: 'शाबाश! दर्ज हो गया।',
    recordSpeech: 'बच्चे की आवाज़ रिकॉर्ड करें',
    invalidLink: 'यह लिंक सही नहीं है। आशा दीदी से नया QR कोड लें।',
    noPlan: 'अभी कोई घर का खेल नहीं है।',
  },
}
