<!DOCTYPE html>
<html>
  <head>
    <base target="_top">
    <style>
      * { box-sizing: border-box; }
      body { 
        font-family: Arial, sans-serif; 
        margin: 0;
        padding: 15px;
        width: 100%;
        overflow-x: hidden;
      }
      label { display:block; margin-top:12px; font-weight:600; }
      select, textarea, input, button { width: 100%; box-sizing: border-box; }
      textarea { min-height: 80px; }
      button { margin-top: 12px; padding: 8px; }
      #result { color:#0a7f2c; margin-top:10px; white-space:pre-wrap; }
      #error { color:#b30000; margin-top:10px; white-space:pre-wrap; }
      fieldset { margin-top:12px; border:1px solid #ddd; border-radius:4px; padding:10px; }
      legend { font-weight:bold; }
      .stats { font-size:13px; color:#444; }
      .stats span { display:block; }
      .note { font-size:12px; color:#555; }
      .hidden { display:none; }
      #previewIds { margin-top:12px; padding:10px; background:#f5f5f5; border-radius:4px; max-height:200px; overflow-y:auto; }
      #previewIds.empty { color:#888; font-style:italic; }
      #previewIds .count { font-weight:bold; margin-bottom:8px; }
      #previewIds .ids-list { font-family:monospace; font-size:12px; line-height:1.6; word-break:break-all; }
      #previewIds .duplicates-warning { margin-top:8px; padding:8px; background:#fff3cd; border:1px solid #ffc107; border-radius:4px; font-size:12px; }
      #previewIds .duplicates-warning strong { color:#856404; }
      #previewIds .duplicates-details { margin-top:4px; font-size:11px; color:#856404; }
      #previewMessage { margin-top:12px; padding:10px; background:#f0f8ff; border:1px solid #b0d4f1; border-radius:4px; }
      #previewMessage.empty { background:#f5f5f5; color:#888; font-style:italic; }
      #previewMessage .preview-header { font-weight:bold; margin-bottom:8px; color:#0066cc; }
      #previewMessage .preview-text { white-space:pre-wrap; word-wrap:break-word; padding:8px; background:white; border:1px solid #ddd; border-radius:4px; margin:8px 0; font-size:13px; line-height:1.5; }
      #previewMessage .preview-info { font-size:12px; color:#555; margin-top:8px; }
      #previewMessage .preview-info span { display:block; margin-top:4px; }
      #previewMessage .preview-note { font-size:11px; color:#888; margin-top:8px; font-style:italic; }
      #loadingIndicator { 
        display:none; 
        margin-top:12px; 
        padding:12px; 
        background:#e8f4f8; 
        border:1px solid #b0d4f1; 
        border-radius:4px; 
        text-align:center; 
        font-size:13px; 
        color:#0066cc; 
      }
      #loadingIndicator.active { display:block; }
      #loadingIndicator .spinner { 
        display:inline-block; 
        width:16px; 
        height:16px; 
        border:2px solid #b0d4f1; 
        border-top-color:#0066cc; 
        border-radius:50%; 
        animation:spin 0.8s linear infinite; 
        margin-right:8px; 
        vertical-align:middle; 
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
    </style>
  </head>
  <body>
    <h3>Массовая отправка SMS</h3>
    <div id="stats" class="stats"></div>
    <form id="bulkSmsForm">
      <fieldset>
        <legend>Кому отправлять</legend>
        <label><input type="radio" name="mode" value="selected" checked> Выбранные ID</label>
        <label><input type="radio" name="mode" value="upcoming"> Клиенты с платежом в ближайшие <input type="number" id="daysBefore" min="0" value="2" style="width:60px; display:inline-block;"> дней</label>
        <div id="minRemainContainer" style="display:none; margin-left:24px; margin-top:4px;">
          <label style="font-weight:normal; font-size:13px;">
            Минимальный остаток по кредиту: <input type="number" id="minRemainAmount" min="0" step="0.01" value="100" style="width:100px; display:inline-block;"> руб.
          </label>
          <div class="note" style="font-size:11px; margin-top:2px;">SMS будут отправлены только клиентам с остатком по кредиту не менее указанной суммы</div>
        </div>
        <label><input type="radio" name="mode" value="overdue"> Все должники (есть просрочка)</label>
        <div id="minOverdueContainer" style="display:none; margin-left:24px; margin-top:4px;">
          <label style="font-weight:normal; font-size:13px;">
            Минимальная сумма задолженности: <input type="number" id="minOverdueAmount" min="0" step="0.01" value="100" style="width:100px; display:inline-block;"> руб.
          </label>
          <div class="note" style="font-size:11px; margin-top:2px;">SMS будут отправлены только должникам с задолженностью не менее указанной суммы</div>
        </div>
        <label><input type="radio" name="mode" value="all"> Все клиенты с включенными SMS</label>
        <div id="idsContainer">
          <textarea id="creditIds" placeholder="Введите ID через пробел, запятую или с новой строки (например: ID12, 45, 78)"></textarea>
          <div class="note">Пустые значения будут проигнорированы. Формат ID автоматически нормализуется.</div>
        </div>
      </fieldset>

      <label for="templateSelect">Шаблон</label>
      <select id="templateSelect" name="templateCode"></select>
      <div class="note" id="templateNote"></div>

      <label for="customMessage">Индивидуальный текст (опционально)</label>
      <textarea id="customMessage" name="customMessage" placeholder="Если поле пустое, используется выбранный шаблон."></textarea>

      <fieldset>
        <legend>Настройки рассылки</legend>
        <label>
          <input type="checkbox" id="respectSmsOptIn" name="respectSmsOptIn" checked>
          Учитывать настройку SMS для клиента (столбец "SMS" - Да/Нет)
        </label>
        <div class="note">Если включено, SMS отправляются только клиентам с включенной рассылкой (столбец "SMS" = "Да"). Если выключено, SMS отправляются всем выбранным клиентам независимо от настройки.</div>
        <label style="margin-top:12px;">
          <input type="checkbox" id="skipIfSentToday" name="skipIfSentToday" checked>
          Пропускать клиентов, которым уже отправлен этот шаблон сегодня
        </label>
        <div class="note">Если включено, клиенты, которым уже был отправлен выбранный шаблон сегодня при массовой рассылке, будут пропущены.</div>
      </fieldset>

      <div id="loadingIndicator">
        <span class="spinner"></span>
        <span>Формирование списка рассылки...</span>
      </div>
      
      <div id="previewIds" class="empty">
        <div class="count">Клиентов для отправки: 0</div>
        <div class="ids-list">Измените настройки для просмотра списка ID</div>
      </div>

      <div id="previewMessage" class="empty">
        <div class="preview-header">Предпросмотр SMS</div>
        <div class="preview-text">Выберите шаблон и настройки для просмотра</div>
      </div>

      <button type="submit" id="submitBtn">Отправить</button>
      <button type="button" id="stopBtn" style="display:none; background:#d9534f; color:white;">Остановить рассылку</button>
      <div id="progressInfo" style="display:none; margin-top:8px; padding:8px; background:#e8f4f8; border-radius:4px; font-size:12px;">
        <div><strong>Рассылка в процессе...</strong></div>
        <div id="progressText" style="margin-top:4px;">Обработано: 0 из 0</div>
        <div style="margin-top:4px; font-size:11px; color:#d9534f; font-weight:bold;">⚠ ВНИМАНИЕ: Не закрывайте это окно до завершения рассылки! Закрытие прервет процесс.</div>
      </div>
    </form>
    <div id="result"></div>
    <div id="error"></div>

    <script>
      var bulkData = null;

      function initBulk() {
        google.script.run
          .withSuccessHandler(function(data) {
            bulkData = data || {};
            renderStats();
            populateTemplateSelect();
          })
          .withFailureHandler(showError)
          .getSmsBulkFormData();
      }

      function renderStats() {
        var stats = (bulkData && bulkData.stats) || {};
        var container = document.getElementById('stats');
        container.innerHTML = [
          'Всего клиентов: ' + (stats.totalCredits || 0),
          'SMS включены: ' + (stats.smsEnabled || 0),
          'С просрочкой: ' + (stats.withOverdue || 0),
          'С ближайшими платежами: ' + (stats.withUpcoming || 0)
        ].map(function(line){ return '<span>' + line + '</span>'; }).join('');
      }

      function populateTemplateSelect() {
        var select = document.getElementById('templateSelect');
        select.innerHTML = '';
        var templates = (bulkData && bulkData.templates) || [];
        if (!templates.length) {
          var opt = document.createElement('option');
          opt.value = '';
          opt.textContent = 'Шаблоны не найдены';
          select.appendChild(opt);
          select.disabled = true;
          return;
        }
        templates.forEach(function(t) {
          var opt = document.createElement('option');
          opt.value = t.code;
          opt.textContent = t.name || t.code;
          if (bulkData.defaultTemplate && t.code === bulkData.defaultTemplate) {
            opt.selected = true;
          }
          select.appendChild(opt);
        });
        select.disabled = false;
        updateTemplateNote();
      }

      function updateTemplateNote() {
        var code = document.getElementById('templateSelect').value;
        var tpl = (bulkData && bulkData.templates || []).find(function(t){ return t.code === code; });
        document.getElementById('templateNote').textContent = tpl && tpl.description ? tpl.description : '';
        updatePreviewMessage();
      }
      
      function updatePreviewMessage() {
        var templateCode = document.getElementById('templateSelect').value;
        var customMessage = document.getElementById('customMessage').value;
        var mode = document.querySelector('input[name="mode"]:checked').value;
        
        if (!templateCode && !customMessage.trim()) {
          var container = document.getElementById('previewMessage');
          container.classList.add('empty');
          container.innerHTML = '<div class="preview-header">Предпросмотр SMS</div><div class="preview-text">Выберите шаблон или введите текст для просмотра</div>';
          return;
        }
        
        var mode = document.querySelector('input[name="mode"]:checked').value;
        var payload = {
          mode: mode,
          templateCode: templateCode,
          customMessage: customMessage,
          creditIds: document.getElementById('creditIds').value,
          daysBefore: Number(document.getElementById('daysBefore').value),
          respectSmsOptIn: document.getElementById('respectSmsOptIn').checked,
          skipIfSentToday: document.getElementById('skipIfSentToday').checked,
          minRemainAmount: mode === 'upcoming' ? Number(document.getElementById('minRemainAmount').value) : 0,
          minOverdueAmount: mode === 'overdue' ? Number(document.getElementById('minOverdueAmount').value) : 0
        };
        
        google.script.run
          .withSuccessHandler(function(result) {
            var container = document.getElementById('previewMessage');
            if (!result.success) {
              container.classList.add('empty');
              container.innerHTML = '<div class="preview-header">Предпросмотр SMS</div><div class="preview-text">' + (result.error || 'Ошибка загрузки предпросмотра') + '</div>';
              return;
            }
            
            container.classList.remove('empty');
            var smsInfo = result.smsInfo || {};
            var smsCountText = result.smsCount || 1;
            var isWarning = smsCountText > 1;
            var smsCountClass = isWarning ? ' style="color:#d9534f; font-weight:bold;"' : '';
            
            container.innerHTML = 
              '<div class="preview-header">Предпросмотр SMS</div>' +
              '<div class="preview-text">' + escapeHtml(result.message || '') + '</div>' +
              '<div class="preview-info">' +
                '<span' + smsCountClass + '>Количество SMS: ' + smsCountText + '</span>' +
                '<span>Символов: ' + (smsInfo.chars || 0) + '</span>' +
                '<span>Тип: ' + (smsInfo.isCyrillic ? 'Кириллица (70 символов = 1 SMS, далее по 67)' : 'Латиница (160 символов = 1 SMS)') + '</span>' +
                '<span>Получателей: ' + (result.totalRecipients || 0) + 
                (result.duplicates && result.duplicates.found && result.uniqueRecipients < result.totalRecipients ? 
                  ' (уникальных номеров: ' + result.uniqueRecipients + ')' : '') + '</span>' +
              '</div>' +
              '<div class="preview-note">' + (result.note || '') + '</div>';
          })
          .withFailureHandler(function(error) {
            var container = document.getElementById('previewMessage');
            container.classList.add('empty');
            container.innerHTML = '<div class="preview-header">Предпросмотр SMS</div><div class="preview-text">Ошибка: ' + (error && error.message ? error.message : String(error)) + '</div>';
          })
          .getSmsBulkPreview(payload);
      }
      
      function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      }

      function updateModeVisibility() {
        var mode = document.querySelector('input[name="mode"]:checked').value;
        document.getElementById('idsContainer').classList.toggle('hidden', mode !== 'selected');
        document.getElementById('daysBefore').disabled = mode !== 'upcoming';
        document.getElementById('minRemainContainer').style.display = mode === 'upcoming' ? 'block' : 'none';
        document.getElementById('minOverdueContainer').style.display = mode === 'overdue' ? 'block' : 'none';
        
        // Автоматически выбираем шаблон по умолчанию в зависимости от режима
        var defaultTemplateCode = 'UPCOMING_2_DAYS';
        if (mode === 'overdue') {
          defaultTemplateCode = 'OVERDUE_DAILY';
        } else if (mode === 'upcoming') {
          defaultTemplateCode = 'UPCOMING_2_DAYS';
        }
        
        var select = document.getElementById('templateSelect');
        if (select && select.options.length > 0) {
          // Проверяем, существует ли шаблон по умолчанию в списке
          var hasDefaultTemplate = Array.prototype.slice.call(select.options).some(function(opt) {
            return opt.value === defaultTemplateCode;
          });
          if (hasDefaultTemplate) {
            select.value = defaultTemplateCode;
            updateTemplateNote();
          }
        }
        
        updatePreviewIds();
        updatePreviewMessage();
      }

      function updatePreviewIds() {
        var mode = document.querySelector('input[name="mode"]:checked').value;
        var payload = {
          mode: mode,
          creditIds: document.getElementById('creditIds').value,
          daysBefore: Number(document.getElementById('daysBefore').value),
          respectSmsOptIn: document.getElementById('respectSmsOptIn').checked,
          minRemainAmount: mode === 'upcoming' ? Number(document.getElementById('minRemainAmount').value) : 0,
          minOverdueAmount: mode === 'overdue' ? Number(document.getElementById('minOverdueAmount').value) : 0
        };
        
        // Показываем индикатор загрузки для режимов "upcoming" (напоминание о платеже) и "overdue" (должники)
        var loadingIndicator = document.getElementById('loadingIndicator');
        if (mode === 'upcoming' || mode === 'overdue') {
          loadingIndicator.classList.add('active');
        }
        
        google.script.run
          .withSuccessHandler(function(result) {
            // Скрываем индикатор загрузки
            loadingIndicator.classList.remove('active');
            
            var container = document.getElementById('previewIds');
            var count = result.count || 0;
            var uniqueCount = result.uniqueCount || count;
            var ids = result.ids || [];
            var duplicates = result.duplicates || {};
            
            container.classList.toggle('empty', count === 0);
            
            var countText = 'Клиентов для отправки: ' + count;
            if (duplicates.found && uniqueCount < count) {
              countText += ' (уникальных номеров: ' + uniqueCount + ')';
            }
            container.querySelector('.count').textContent = countText;
            
            var idsList = container.querySelector('.ids-list');
            if (count === 0) {
              idsList.textContent = 'Нет клиентов, соответствующих выбранным критериям';
            } else {
              idsList.textContent = ids.join(', ');
            }
            
            // Показываем предупреждение о дубликатах
            var existingWarning = container.querySelector('.duplicates-warning');
            if (existingWarning) {
              existingWarning.remove();
            }
            
            if (duplicates.found && duplicates.details && duplicates.details.length > 0) {
              var warning = document.createElement('div');
              warning.className = 'duplicates-warning';
              var detailsText = duplicates.details.map(function(dup) {
                var clients = dup.clients.map(function(c) { return c.id + (c.fio ? ' (' + c.fio + ')' : ''); }).join(', ');
                return 'Номер ' + dup.phone + ': ' + clients;
              }).join('; ');
              warning.innerHTML = '<strong>⚠ Обнаружены дубликаты номеров:</strong><div class="duplicates-details">' + 
                'Найдено ' + duplicates.count + ' номеров с дубликатами. SMS будет отправлено только один раз на каждый номер. ' +
                'Детали: ' + detailsText + '</div>';
              container.appendChild(warning);
            }
          })
          .withFailureHandler(function(error) {
            // Скрываем индикатор загрузки при ошибке
            loadingIndicator.classList.remove('active');
            document.getElementById('previewIds').querySelector('.ids-list').textContent = 'Ошибка загрузки: ' + (error && error.message ? error.message : String(error));
          })
          .getSmsBulkPreviewIds(payload);
      }

      function showError(error) {
        document.getElementById('error').textContent = error && error.message ? error.message : String(error || '');
      }

      document.getElementById('templateSelect').addEventListener('change', updateTemplateNote);
      document.getElementById('customMessage').addEventListener('input', updatePreviewMessage);
      Array.prototype.slice.call(document.querySelectorAll('input[name="mode"]')).forEach(function(el) {
        el.addEventListener('change', function() {
          updateModeVisibility();
        });
      });
      document.getElementById('daysBefore').addEventListener('input', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('daysBefore').addEventListener('change', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('creditIds').addEventListener('input', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('respectSmsOptIn').addEventListener('change', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('skipIfSentToday').addEventListener('change', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('minRemainAmount').addEventListener('input', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('minRemainAmount').addEventListener('change', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('minOverdueAmount').addEventListener('input', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });
      document.getElementById('minOverdueAmount').addEventListener('change', function() {
        updatePreviewIds();
        updatePreviewMessage();
      });

      var isSending = false;
      var progressInterval = null;
      
      // Защита от закрытия окна во время рассылки
      window.addEventListener('beforeunload', function(e) {
        if (isSending) {
          e.preventDefault();
          e.returnValue = 'Идет рассылка SMS. Если вы закроете окно, рассылка будет прервана. Вы уверены?';
          return e.returnValue;
        }
      });
      
      function startSending() {
        isSending = true;
        document.getElementById('submitBtn').disabled = true;
        document.getElementById('stopBtn').style.display = 'block';
        document.getElementById('progressInfo').style.display = 'block';
        document.getElementById('result').textContent = '';
        document.getElementById('error').textContent = '';
        
        // Запускаем периодическую проверку прогресса
        progressInterval = setInterval(function() {
          if (!isSending) {
            clearInterval(progressInterval);
            return;
          }
          // Можно добавить функцию для получения текущего прогресса, если нужно
        }, 500);
      }
      
      function stopSending() {
        isSending = false;
        document.getElementById('submitBtn').disabled = false;
        document.getElementById('stopBtn').style.display = 'none';
        document.getElementById('progressInfo').style.display = 'none';
        if (progressInterval) {
          clearInterval(progressInterval);
          progressInterval = null;
        }
      }
      
      document.getElementById('stopBtn').addEventListener('click', function() {
        if (confirm('Остановить рассылку SMS? Уже отправленные SMS не будут отменены.')) {
          google.script.run
            .withSuccessHandler(function(result) {
              document.getElementById('progressText').textContent = 'Остановка рассылки...';
            })
            .withFailureHandler(function(error) {
              showError('Ошибка при остановке: ' + (error && error.message ? error.message : String(error)));
            })
            .setSmsBulkStopFlag(true);
        }
      });
      
      document.getElementById('bulkSmsForm').addEventListener('submit', function(e) {
        e.preventDefault();
        document.getElementById('result').textContent = '';
        document.getElementById('error').textContent = '';
        var templateCode = document.getElementById('templateSelect').value;
        if (!templateCode) {
          showError('Выберите шаблон');
          return;
        }
        
        startSending();
        
        var mode = document.querySelector('input[name="mode"]:checked').value;
        var payload = {
          mode: mode,
          templateCode: templateCode,
          customMessage: document.getElementById('customMessage').value,
          creditIds: document.getElementById('creditIds').value,
          daysBefore: Number(document.getElementById('daysBefore').value),
          respectSmsOptIn: document.getElementById('respectSmsOptIn').checked,
          minRemainAmount: mode === 'upcoming' ? Number(document.getElementById('minRemainAmount').value) : 0,
          minOverdueAmount: mode === 'overdue' ? Number(document.getElementById('minOverdueAmount').value) : 0
        };
        
        // Показываем индикатор загрузки при формировании списка для режимов "upcoming" (напоминание о платеже) и "overdue" (должники)
        var loadingIndicator = document.getElementById('loadingIndicator');
        if (mode === 'upcoming' || mode === 'overdue') {
          loadingIndicator.classList.add('active');
        }
        
        // Получаем общее количество получателей для отображения прогресса
        google.script.run
          .withSuccessHandler(function(previewResult) {
            // Скрываем индикатор загрузки после получения результата
            loadingIndicator.classList.remove('active');
            var total = previewResult.uniqueCount || previewResult.count || 0;
            document.getElementById('progressText').textContent = 'Обработано: 0 из ' + total;
          })
          .withFailureHandler(function(error) {
            // Скрываем индикатор загрузки при ошибке
            loadingIndicator.classList.remove('active');
          })
          .getSmsBulkPreviewIds(payload);
        
        google.script.run
          .withSuccessHandler(function(summary) {
            stopSending();
            var text = [];
            
            // Информация об остановке
            if (summary.stopped) {
              text.push('⚠ ' + (summary.message || 'Рассылка прервана пользователем'));
              text.push('Обработано: ' + (summary.processed || 0) + ' из ' + (summary.total || 0));
            }
            
            text.push('Всего попыток: ' + (summary.total || 0));
            text.push('Обработано: ' + (summary.processed || summary.total || 0));
            text.push('Успешно: ' + (summary.success || 0));
            text.push('Ошибок: ' + (summary.failed || 0));
            
            // Добавляем информацию о дубликатах
            if (summary.duplicates && summary.duplicates.found) {
              var skipped = (summary.details || []).filter(function(d) { return d.status === 'SKIPPED_DUPLICATE'; }).length;
              if (skipped > 0) {
                text.push('Пропущено дубликатов: ' + skipped);
              }
              if (summary.duplicates.count > 0) {
                text.push('Найдено номеров с дубликатами: ' + summary.duplicates.count);
                text.push('Уникальных номеров: ' + summary.duplicates.uniquePhones);
              }
            }
            
            document.getElementById('result').textContent = text.join('\n');
            
            if (summary.failed) {
              var errors = (summary.details || []).filter(function(d){ return !d.success && d.status !== 'SKIPPED_DUPLICATE'; });
              if (errors.length) {
                document.getElementById('result').textContent += '\nНеудачи:\n' + errors.slice(0, 10).map(function(err) {
                  return (err.creditId || '?') + ': ' + (err.status || '') + ' ' + (err.response || '');
                }).join('\n');
              }
            }
            
            // Показываем информацию о пропущенных дубликатах
            if (summary.duplicates && summary.duplicates.found) {
              var skipped = (summary.details || []).filter(function(d) { return d.status === 'SKIPPED_DUPLICATE'; });
              if (skipped.length > 0) {
                document.getElementById('result').textContent += '\n\nПропущенные дубликаты:\n' + 
                  skipped.slice(0, 10).map(function(s) {
                    return (s.creditId || '?') + ' (' + (s.fio || '') + '): ' + (s.response || '');
                  }).join('\n');
                if (skipped.length > 10) {
                  document.getElementById('result').textContent += '\n... и еще ' + (skipped.length - 10) + ' дубликатов';
                }
              }
            }
          })
          .withFailureHandler(function(error) {
            stopSending();
            showError(error);
          })
          .runSmsBulkFromUi(payload);
      });

      document.addEventListener('DOMContentLoaded', function() {
        updateModeVisibility();
        initBulk();
        // Обновляем список ID после загрузки данных
        setTimeout(function() {
          updatePreviewIds();
          setTimeout(updatePreviewMessage, 300);
        }, 500);
      });
    </script>
  </body>
</html>

