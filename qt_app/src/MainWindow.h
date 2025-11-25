#pragma once

#include <QLabel>
#include <QMainWindow>
#include <QMap>
#include <QStackedWidget>

#include "SectionPanel.h"

class QTextEdit;

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);

private slots:
    void showLanding();
    void startListening();
    void startReading();
    void submitAnswers();
    void previewAnswers();
    void clearActive();
    void saveAnswers();
    void pasteAnswerKeys();
    void toggleHideAnswers();

private:
    QStackedWidget *stack_ = nullptr;
    SectionPanel *listeningPanel_ = nullptr;
    SectionPanel *readingPanel_ = nullptr;
    QLabel *scoreLabel_ = nullptr;
    QPushButton *hideButton_ = nullptr;
    bool answersHidden_ = false;

    QWidget *buildLandingPage();
    QWidget *buildSectionPage(SectionPanel *panel);
    SectionPanel *activePanel(QString *sectionName = nullptr) const;
    void updateScoreLabel(const QString &text);
    double lookupBand(const QString &sectionName, int correct) const;
    QMap<int, QString> parseAnswersFromDialog();
    void applyKeyVisibility();
    QStringList collectAnswers(const SectionPanel *panel) const;
};

