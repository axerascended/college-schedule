# CI/CD: инструкция по работе с деплоем

Полное руководство по непрерывной интеграции и доставке проекта **college-schedule** на виртуальную машину Yandex Cloud через GitHub Actions.

---

## 1. Общая схема

```
Разработчик → git push (master) → GitHub Actions
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
              job: test                           job: deploy
         (pytest на runner)              (SSH → ВМ → deploy.sh)
                    │                                   │
                    └──────── deploy только если test OK ┘
```

| Этап | Где выполняется | Что происходит |
|------|-----------------|----------------|
| **CI (test)** | GitHub-hosted runner (Ubuntu) | Установка Python 3.11, `pip install`, `pytest` |
| **CD (deploy)** | ВМ Yandex Cloud | `git pull`, зависимости, миграции, `systemctl restart schedule` |

**Репозиторий:** https://github.com/axerascended/college-schedule  
**Workflow:** `.github/workflows/deploy.yml`  
**Actions:** https://github.com/axerascended/college-schedule/actions

---

## 2. Инфраструктура на Yandex Cloud

| Параметр | Значение |
|----------|----------|
| Имя ВМ | `schedule-diploma` |
| Зона | `ru-central1-a` |
| Ресурсы | 2 vCPU, 2 GB RAM, 15 GB HDD |
| Пользователь SSH | `yc-user` |
| Публичный IP | см. `yc compute instance get schedule-diploma` (может меняться после stop/start без статического IP) |
| Security group | `schedule-diploma-sg` (порты 22, 80, 443, 8000 входящие; egress в интернет) |
| Каталог приложения | `/home/yc-user/college-schedule` |
| systemd-сервис | `schedule` |
| URL приложения | `http://<IP>:8000/login` |

### Просмотр IP через CLI

```powershell
yc compute instance get schedule-diploma --format json
```

Поле: `network_interfaces[0].primary_v4_address.one_to_one_nat.address`

---

## 3. Файлы деплоя в репозитории

| Файл | Назначение |
|------|------------|
| `.github/workflows/deploy.yml` | Pipeline: тесты + SSH-деплой |
| `deploy/install-server.sh` | **Однократная** первичная настройка ВМ |
| `deploy/deploy.sh` | Скрипт, вызываемый при каждом деплое |
| `deploy/schedule.service` | Unit systemd для uvicorn |
| `.gitattributes` | Принудительные LF для `*.sh` (важно для Linux) |

---

## 4. Секреты GitHub Actions

Задаются в репозитории: **Settings → Secrets and variables → Actions → Repository secrets**.

| Секрет | Описание | Пример |
|--------|----------|--------|
| `DEPLOY_HOST` | Публичный IP ВМ | `51.250.11.246` |
| `DEPLOY_USER` | SSH-пользователь | `yc-user` |
| `DEPLOY_SSH_KEY` | **Приватный** SSH-ключ (весь файл, включая `BEGIN`/`END`) | `~/.ssh/yc_schedule_diploma` |

### Установка секретов через GitHub CLI

```powershell
gh secret set DEPLOY_HOST --body "ВАШ_IP"
gh secret set DEPLOY_USER --body "yc-user"
Get-Content $env:USERPROFILE\.ssh\yc_schedule_diploma -Raw | gh secret set DEPLOY_SSH_KEY
```

### Проверка списка секретов

```powershell
gh secret list --repo axerascended/college-schedule
```

**Важно:** секреты не попадают в git. Не коммитьте `.env`, приватные ключи и токены.

---

## 5. Когда запускается pipeline

| Триггер | Условие |
|---------|---------|
| **push** | Ветка `master` |
| **workflow_dispatch** | Ручной запуск в Actions → CI/CD → Run workflow |

Деплой выполняется **только** если job `test` завершился успешно.

---

## 6. Ежедневная работа разработчика

### Стандартный цикл

```powershell
cd C:\Users\ol4ik\Projects\Kyrs
git checkout master
git pull origin master

# ... правки кода ...

git add .
git commit -m "Описание изменений"
git push origin master
```

После push:

1. Откройте **Actions** в GitHub.
2. Дождитесь зелёной галочки у workflow **CI/CD** (~30–60 с).
3. Проверьте сайт: `http://<DEPLOY_HOST>:8000/login`

### Локальная проверка до push (рекомендуется)

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pytest
```

Если тесты падают локально — deploy **не запустится** (job `deploy` зависит от `test`).

---

## 7. Ручной деплой без изменений в коде

GitHub → **Actions** → **CI/CD** → **Run workflow** → ветка `master` → **Run workflow**.

Или через CLI:

```powershell
gh workflow run "CI/CD" --repo axerascended/college-schedule --ref master
gh run list --repo axerascended/college-schedule --limit 3
gh run watch
```

---

## 8. Что делает `deploy/deploy.sh` на сервере

1. `git fetch` + `git reset --hard origin/master` — код строго как на GitHub.
2. `pip install -r requirements.txt` в `.venv`.
3. `alembic upgrade head` — миграции БД.
4. `sudo systemctl restart schedule` — перезапуск приложения.

**Не перезаписывается:** файл `.env` на сервере (создаётся один раз при `install-server.sh`).

**Не удаляется:** `data/schedule.db` и флаг `data/.seeded` (повторный seed не запускается).

---

## 9. Первичная настройка новой ВМ (один раз)

Если ВМ создана заново или каталог приложения пуст:

```powershell
ssh -i $env:USERPROFILE\.ssh\yc_schedule_diploma yc-user@<IP>
```

На сервере:

```bash
git clone https://github.com/axerascended/college-schedule.git /home/yc-user/college-schedule
cd /home/yc-user/college-schedule
sed -i 's/\r$//' deploy/*.sh   # если скрипты с Windows-переводами строк
chmod +x deploy/*.sh
bash deploy/install-server.sh
```

После этого обновите секрет `DEPLOY_HOST`, если IP изменился.

### Требования к сети ВМ

- Security group должна разрешать **egress** в интернет (для `git clone`, `pip`).
- Входящие: 22 (SSH), 8000 (приложение), при необходимости 80/443.

---

## 10. Управление приложением на ВМ (SSH)

```bash
# Статус
sudo systemctl status schedule

# Перезапуск
sudo systemctl restart schedule

# Логи
sudo journalctl -u schedule -f

# Остановка / запуск
sudo systemctl stop schedule
sudo systemctl start schedule
```

Просмотр `.env` (только на сервере):

```bash
cat /home/yc-user/college-schedule/.env
```

---

## 11. Диагностика сбоев CI/CD

### Job `test` упал

| Симптом | Действие |
|---------|----------|
| Ошибка импорта / pytest | Исправить код, запустить `pytest` локально |
| Падает один тест | См. лог шага **Run tests** в Actions |

```powershell
gh run view <RUN_ID> --repo axerascended/college-schedule --log-failed
```

### Job `deploy` упал

| Симптом | Возможная причина | Решение |
|---------|-------------------|---------|
| `Permission denied (publickey)` | Неверный `DEPLOY_SSH_KEY` или ключ не на ВМ | Проверить секрет; пересоздать ВМ с `--ssh-key` или добавить ключ в `~/.ssh/authorized_keys` |
| `Connection timed out` | Неверный IP, ВМ выключена, SG блокирует 22 | Проверить IP, `yc compute instance list`, security group |
| `deploy.sh: No such file` | Не выполнен `install-server.sh` | Запустить первичную настройку (раздел 9) |
| `set: pipefail: invalid option` | CRLF в shell-скриптах | `sed -i 's/\r$//' deploy/*.sh` на сервере; в репозитории — `.gitattributes` |
| `git fetch` / network errors | Нет egress в SG | Добавить egress rule в `schedule-diploma-sg` |

### Проверка SSH с локального ПК

```powershell
ssh -i $env:USERPROFILE\.ssh\yc_schedule_diploma yc-user@<IP> "systemctl is-active schedule"
```

Ожидается: `active`.

---

## 12. Смена IP или SSH-ключа

1. Узнать новый IP: `yc compute instance get schedule-diploma`.
2. Обновить секрет: `gh secret set DEPLOY_HOST --body "НОВЫЙ_IP"`.
3. При смене ключа — обновить `DEPLOY_SSH_KEY` и публичный ключ на ВМ.
4. Запустить workflow вручную или сделать пустой commit + push.

---

## 13. Демо-учётные записи на продакшене

После `install-server.sh` (seed один раз):

| Роль | Email | Пароль |
|------|-------|--------|
| Admin | admin@college.local | admin123 |
| Student | student@college.local | student123 |
| Teacher | teacher@college.local | teacher123 |

Для диплома смените пароли или создайте отдельных пользователей через админку.

---

## 14. Экономия на Yandex Cloud

```powershell
yc compute instance stop schedule-diploma   # остановить ВМ
yc compute instance start schedule-diploma  # запустить (IP может смениться!)
```

После start — обновите `DEPLOY_HOST` в секретах GitHub.

---

## 15. Что не коммитить (см. `.gitignore`)

- `.env` — локальные и серверные секреты
- `.venv/`, `__pycache__/`
- `schedule.db`, каталог `data/` (БД на сервере)
- Локальные копии SSH-ключей для деплоя (`*.pem`, `deploy.secrets`, см. `.gitignore`)

Полная инструкция по приложению локально: **[ИНСТРУКЦИЯ.md](ИНСТРУКЦИЯ.md)**.

---

## 16. Краткая шпаргалка

| Задача | Команда / место |
|--------|-----------------|
| Задеплоить код | `git push origin master` |
| Ручной деплой | Actions → Run workflow |
| Логи pipeline | GitHub → Actions → выбрать run |
| Логи приложения | `journalctl -u schedule -f` на ВМ |
| Секреты | GitHub Settings → Actions secrets |
| IP ВМ | `yc compute instance get schedule-diploma` |
| Сайт | `http://<IP>:8000/login` |
