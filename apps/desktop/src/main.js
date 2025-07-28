const { app, BrowserWindow, Menu, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');

// Keep a global reference of the window object
let mainWindow;
let recentFiles = [];

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    show: false
  });

  // Load the app
  mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Set up application menu
  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open EDI File...',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            openFile();
          }
        },
        {
          label: 'Open Recent',
          submenu: getRecentFilesMenu()
        },
        { type: 'separator' },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            mainWindow.webContents.send('menu-save');
          }
        },
        {
          label: 'Save As...',
          accelerator: 'CmdOrCtrl+Shift+S',
          click: () => {
            saveFileAs();
          }
        },
        { type: 'separator' },
        {
          label: 'Export JSON...',
          click: () => {
            mainWindow.webContents.send('menu-export-json');
          }
        },
        { type: 'separator' },
        {
          role: 'quit'
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Raw/Tree View',
          accelerator: 'CmdOrCtrl+T',
          click: () => {
            mainWindow.webContents.send('menu-toggle-view');
          }
        },
        {
          label: 'Toggle Validation Panel',
          accelerator: 'CmdOrCtrl+E',
          click: () => {
            mainWindow.webContents.send('menu-toggle-errors');
          }
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'Validate File',
          accelerator: 'CmdOrCtrl+Shift+V',
          click: () => {
            mainWindow.webContents.send('menu-validate');
          }
        },
        {
          label: 'Parse File',
          accelerator: 'CmdOrCtrl+Shift+P',
          click: () => {
            mainWindow.webContents.send('menu-parse');
          }
        },
        { type: 'separator' },
        {
          label: 'Settings...',
          click: () => {
            mainWindow.webContents.send('menu-settings');
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About EDI CLI',
          click: () => {
            showAbout();
          }
        },
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/your-org/edi-cli/docs');
          }
        },
        {
          label: 'Report Issue',
          click: () => {
            shell.openExternal('https://github.com/your-org/edi-cli/issues');
          }
        }
      ]
    }
  ];

  // macOS specific menu adjustments
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    });

    // Window menu
    template.push({
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function getRecentFilesMenu() {
  if (recentFiles.length === 0) {
    return [{ label: 'No recent files', enabled: false }];
  }

  return recentFiles.map(file => ({
    label: path.basename(file),
    click: () => {
      openSpecificFile(file);
    }
  }));
}

function addToRecentFiles(filePath) {
  // Remove if already exists
  recentFiles = recentFiles.filter(file => file !== filePath);
  
  // Add to beginning
  recentFiles.unshift(filePath);
  
  // Keep only last 10 files
  recentFiles = recentFiles.slice(0, 10);
  
  // Update menu
  createMenu();
}

async function openFile() {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'EDI Files', extensions: ['edi', 'x12', 'txt'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const filePath = result.filePaths[0];
    openSpecificFile(filePath);
  }
}

function openSpecificFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    addToRecentFiles(filePath);
    mainWindow.webContents.send('file-opened', {
      path: filePath,
      content: content,
      name: path.basename(filePath)
    });
  } catch (error) {
    dialog.showErrorBox('Error Opening File', `Could not open file: ${error.message}`);
  }
}

async function saveFileAs() {
  const result = await dialog.showSaveDialog(mainWindow, {
    filters: [
      { name: 'EDI Files', extensions: ['edi'] },
      { name: 'JSON Files', extensions: ['json'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });

  if (!result.canceled) {
    mainWindow.webContents.send('save-file-as', result.filePath);
  }
}

function showAbout() {
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'About EDI CLI Desktop',
    message: 'EDI CLI Desktop',
    detail: 'Version 0.4.0\n\nPostman for EDI - A developer-friendly tool for parsing, validating, and analyzing EDI files.\n\nBuilt with Electron and the edi-cli parsing engine.',
    buttons: ['OK']
  });
}

// IPC handlers
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    fs.writeFileSync(filePath, content, 'utf8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// App event handlers
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});