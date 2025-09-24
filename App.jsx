/*
React + Tailwind одностраничный лендинг для компании по системам безопасности и охраны.
Инструкции по использованию:
1. В проекте должен быть настроен Tailwind CSS.
2. Установите зависимости (если используете): framer-motion, lucide-react, @/components/ui (shadcn/ui) — опционально.
   Примеры: npm i framer-motion lucide-react
3. Файл — одиночный React-компонент. По желанию разделите на компоненты.
4. Замените плейсхолдеры (LOGO_URL, контакты, логотипы партнёров и клиентов, реквизиты).

Описание:
- Цветовая схема: белый и красный (акцент: --brand-red)
- Структура соответствует заданию: Hero, О компании, Услуги, Проекты, Партнёры, Команда/Ресурсы, Контакты, Футер
- Анимации: framer-motion для аккуратных переходов
- Верстка: Tailwind + grid/flex, адаптивность обеспечена
*/

import React from 'react';
import { motion } from 'framer-motion';
import { Phone, Mail } from 'lucide-react';

const LOGO_URL = '/placeholder-logo.svg'; // замените на ваш логотип
const PARTNERS = [
  { name: 'Партнёр A', logo: '/partner1.svg' },
  { name: 'Партнёр B', logo: '/partner2.svg' },
  { name: 'Партнёр C', logo: '/partner3.svg' }
];
const CLIENTS = [
  { name: 'Клиент A', logo: '/client1.svg' },
  { name: 'Клиент B', logo: '/client2.svg' },
  { name: 'Клиент C', logo: '/client3.svg' }
];

export default function SecurityLanding({
  phone = '+7 (___) ___-__-__',
  email = 'info@example.com',
  address = 'Ваш юридический и фактический адрес',
  inn = '0000000000',
  kpp = '000000000',
  ogrn = '0000000000000',
  contactPerson = 'Должность, ФИО',
  companyName = 'Название вашей компании',
  foundedYear = 2018
}) {
  const currentYear = new Date().getFullYear();

  const services = [
    'Пуско-наладочные работы технологического оборудования',
    'Электромонтажные работы',
    'Монтаж средств АПС и СОУЭ',
    'Создание систем ОПС, СКУД, систем охранного телевидения',
    'Создание систем периметральной защиты',
    'Структированные кабельные системы (СКС)',
    'Разработка сетевой инфраструктуры и ЛВС',
    'Системы автоматического пожаротушения',
    'Общестроительные и кровельные работы',
    'Демонтаж/монтаж металлоконструкций',
    'Изготовление строительных деталей и металлоконструкций',
    'Антикоррозийная защита и покраска'
  ];

  return (
    <div className="min-h-screen bg-white text-gray-900 antialiased">
      {/* Global CSS variables for brand colors */}
      <style>{`:root{--brand-red:#e11d2a}`}</style>

      {/* Fixed header */}
      <header className="fixed w-full bg-white/95 backdrop-blur-sm shadow z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <img src={LOGO_URL} alt="logo" className="h-10 w-auto" />
              <div className="hidden sm:block">
                <div className="text-sm font-semibold">{companyName}</div>
                <div className="text-xs text-gray-500">Строим системы безопасности и охраны</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <a href={`tel:${phone}`} className="inline-flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-white bg-[var(--brand-red)] shadow-sm hover:brightness-95">
                <Phone className="w-4 h-4" />
                <span className="hidden sm:inline">{phone}</span>
              </a>
              <a href={`mailto:${email}`} className="hidden sm:inline text-sm text-gray-600 hover:underline"><Mail className="w-4 h-4 inline mr-2"/>{email}</a>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-24">
        {/* HERO */}
        <section className="relative overflow-hidden">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
                <span className="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-[var(--brand-red)] text-white">[Логотип] {companyName}</span>
                <h1 className="mt-6 text-3xl sm:text-4xl font-extrabold leading-tight">Строим системы безопасности и охраны</h1>
                <p className="mt-4 text-gray-600">Профессиональные решения под ключ: от проектирования до пусконаладочных работ. Гарантируем качество и соблюдение сроков.</p>

                <div className="mt-6 flex flex-col sm:flex-row gap-3">
                  <a href="#contact" className="inline-flex items-center justify-center px-6 py-3 rounded-md bg-[var(--brand-red)] text-white font-semibold shadow hover:brightness-95">Получить коммерческое предложение</a>
                  <a href={`tel:${phone}`} className="inline-flex items-center gap-2 px-5 py-3 rounded-md border border-gray-200 text-gray-700 hover:bg-gray-50">
                    <Phone className="w-4 h-4"/>
                    Позвонить
                  </a>
                </div>

                <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="text-sm">
                    <div className="text-xs text-gray-500">Телефон</div>
                    <div className="font-medium">{phone}</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-xs text-gray-500">Email</div>
                    <div className="font-medium">{email}</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-xs text-gray-500">Опыт на рынке</div>
                    <div className="font-medium">C {foundedYear} г.</div>
                  </div>
                </div>
              </motion.div>

              <motion.div className="order-first lg:order-last" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }}>
                {/* Placeholder illustration / hero image */}
                <div className="w-full rounded-2xl bg-gray-50 p-6 shadow">
                  <img src="/hero-illustration.svg" alt="security" className="w-full h-64 object-cover rounded-md" />
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* ABOUT */}
        <section id="about" className="mt-12">
          <div className="max-w-4xl mx-auto text-center">
            <motion.h2 className="text-2xl font-bold" initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }} transition={{ duration:0.5 }}>О компании</motion.h2>
            <motion.p className="mt-4 text-gray-600" initial={{ opacity:0 }} whileInView={{ opacity:1 }} transition={{ delay:0.1 }}>{`Наша компания успешно работает на рынке с ${foundedYear} года. Мы предлагаем полный цикл работ от проектирования до реализации сложных технических и строительных проектов. Наши специалисты регулярно проходят аттестацию и повышение квалификации для выполнения работ самого высокого уровня.`}</motion.p>
          </div>
        </section>

        {/* SERVICES */}
        <section id="services" className="mt-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.h2 className="text-center text-2xl font-bold" initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }} transition={{ duration:0.5 }}>Ключевые направления деятельности</motion.h2>

            <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {services.map((s, idx) => (
                <motion.div key={idx} className="p-6 bg-white rounded-lg shadow-sm border" whileHover={{ y: -6 }} initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }} transition={{ delay: idx*0.05 }}>
                  <div className="h-10 w-10 rounded-md bg-[var(--brand-red)]/10 flex items-center justify-center text-[var(--brand-red)] font-semibold">{s[0]}</div>
                  <h4 className="mt-4 font-semibold">{s}</h4>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* PROJECTS */}
        <section id="projects" className="mt-16 bg-gray-50 py-10">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.h2 className="text-center text-2xl font-bold" initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>Нам доверяют крупнейшие компании</motion.h2>
            <p className="mt-3 text-center text-gray-600">Наши специалисты имеют успешный опыт выполнения работ на объектах промышленного и гражданского назначения.</p>

            <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6 items-center">
              {CLIENTS.map((c, i) => (
                <div key={i} className="flex items-center justify-center p-3 bg-white rounded-md shadow-sm">
                  <img src={c.logo} alt={c.name} className="max-h-10 object-contain" />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* PARTNERS */}
        <section id="partners" className="mt-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.h2 className="text-center text-2xl font-bold" initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>С нами сотрудничают</motion.h2>
            <p className="mt-3 text-center text-gray-600">Мы благодарны нашим партнёрам за доверие и успешные проекты.</p>

            <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-6">
              {PARTNERS.map((p, i) => (
                <div key={i} className="flex items-center justify-center p-3 bg-white rounded-md shadow-sm">
                  <img src={p.logo} alt={p.name} className="max-h-10 object-contain" />
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* TEAM & RESOURCES */}
        <section id="team" className="mt-16">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <motion.div initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>
              <h3 className="text-2xl font-bold">Профессионализм и надежность</h3>
              <p className="mt-4 text-gray-600">Наша сила — в квалифицированных кадрах и современной материально-технической базе.</p>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 bg-white rounded shadow-sm">
                  <h4 className="font-semibold">Команда</h4>
                  <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                    <li>Квалифицированные инженерно-технические работники (ИТР)</li>
                    <li>Опытные линейные специалисты</li>
                    <li>Слаженная работа отделов: ПТО, снабжения, кадров и бухгалтерии</li>
                  </ul>
                </div>
                <div className="p-4 bg-white rounded shadow-sm">
                  <h4 className="font-semibold">Ресурсы</h4>
                  <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                    <li>Наличие всех необходимых допусков СРО</li>
                    <li>Собственный автотранспорт и современное оборудование</li>
                    <li>Постоянное обновление инструментальной базы</li>
                  </ul>
                </div>
              </div>
            </motion.div>

            <motion.div initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>
              <div className="p-6 bg-white rounded shadow-sm">
                <h4 className="font-semibold">Квалификация и безопасность работ</h4>
                <p className="mt-2 text-sm text-gray-600">Все работы выполняются в соответствии с действующими нормативными документами и под контролем опытных инженеров.</p>
                <div className="mt-4 space-y-3">
                  <div className="text-sm"><span className="font-semibold">Допуски:</span> СРО, сертификаты исполнителей</div>
                  <div className="text-sm"><span className="font-semibold">Оборудование:</span> современная техника и инструменты</div>
                  <div className="text-sm"><span className="font-semibold">Техника безопасности:</span> регламентированные процедуры и обучение персонала</div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* CONTACTS */}
        <section id="contact" className="mt-16 bg-white py-10">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <motion.div initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>
              <h3 className="text-2xl font-bold">Контакты</h3>
              <p className="mt-4 text-gray-600">Адрес: <span className="font-medium">{address}</span></p>
              <p className="mt-2 text-gray-600">Телефон: <a href={`tel:${phone}`} className="text-[var(--brand-red)] font-medium">{phone}</a></p>
              <p className="mt-2 text-gray-600">Email: <a href={`mailto:${email}`} className="text-[var(--brand-red)] font-medium">{email}</a></p>

              <div className="mt-6 p-4 bg-gray-50 rounded">
                <h4 className="font-semibold">Реквизиты</h4>
                <div className="mt-2 text-sm text-gray-600">
                  <div>ИНН: <span className="font-medium">{inn}</span></div>
                  <div>КПП: <span className="font-medium">{kpp}</span></div>
                  <div>ОГРН: <span className="font-medium">{ogrn}</span></div>
                  <div>Контактное лицо: <span className="font-medium">{contactPerson}</span></div>
                </div>
              </div>
            </motion.div>

            <motion.div initial={{ opacity:0, y:10 }} whileInView={{ opacity:1, y:0 }}>
              <h3 className="text-2xl font-bold">Получить коммерческое предложение</h3>
              <p className="mt-2 text-gray-600">Оставьте заявку — мы подготовим КП с учётом требований вашего объекта.</p>

              <form className="mt-4 space-y-3" onSubmit={(e)=>{e.preventDefault(); alert('Заявка отправлена — замените alert на реальную интеграцию.');}}>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <input required name="name" placeholder="Ваше имя" className="w-full px-3 py-2 border rounded" />
                  <input required name="phone" placeholder="Телефон" className="w-full px-3 py-2 border rounded" />
                </div>
                <input name="company" placeholder="Компания (опционально)" className="w-full px-3 py-2 border rounded" />
                <textarea name="details" placeholder="Кратко опишите задачу" rows={4} className="w-full px-3 py-2 border rounded" />
                <button type="submit" className="w-full inline-flex items-center justify-center px-4 py-3 bg-[var(--brand-red)] text-white font-semibold rounded">Отправить заявку</button>
              </form>
            </motion.div>
          </div>
        </section>

        {/* FOOTER */}
        <footer className="mt-16 border-t pt-6 pb-10">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            <div>
              <img src={LOGO_URL} alt="logo" className="h-10" />
              <div className="mt-3 text-sm text-gray-600">{companyName}</div>
              <div className="mt-2 text-sm text-gray-600">Тел: <a href={`tel:${phone}`} className="text-[var(--brand-red)]">{phone}</a> | Email: <a href={`mailto:${email}`} className="text-[var(--brand-red)]">{email}</a></div>
            </div>

            <div className="text-sm text-gray-600">
              <div className="font-semibold">Юридическая информация</div>
              <div className="mt-2">ИНН: {inn}</div>
              <div>КПП: {kpp}</div>
              <div>ОГРН: {ogrn}</div>
            </div>

            <div className="text-sm">
              <div className="mb-2"><a href="#policy" className="text-gray-600 hover:underline">Политика конфиденциальности</a></div>
              <div className="text-gray-500">© {companyName}, {foundedYear} - {currentYear}</div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
